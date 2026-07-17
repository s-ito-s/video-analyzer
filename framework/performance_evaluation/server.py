import concurrent.futures
import datetime
import json
import logging
import random
import sys
import av
import click
import grpc
import numpy as np
from dataclasses import dataclass, field
from google.protobuf.json_format import ParseDict
from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp
from proto.stream.v1.analyzer_pb2_grpc import (
    StreamAnalyzerServiceServicer,
    add_StreamAnalyzerServiceServicer_to_server,
)
from proto.stream.v1.analyzer_pb2 import (
    DeviceStatus,
    EventPicture,
    ObjectPicture,
    StreamAnalyzeRequest,
    StreamAnalyzeResponse,
)
from log.logger import Logger

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
from StreamAnalyzer import StreamAnalyzer

# デバッグ用
import cv2

log_file_name = f"server_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
stream_count = 0

PROCESSING_INTERVAL_MS = 200

@dataclass
class FrameAnalyzerResult:
    is_keyframe: bool = False
    timestamp: Timestamp = field(default_factory=Timestamp)
    thumbnail_data: bytes = b""
    labels: list[str] = field(
        default_factory=list
    )  # ここに設定されたラベルでAI Studio画面上でフィルタリングが可能
    data: dict = field(default_factory=dict)  # 任意のJSONシリアライズ可能なデータ
    score: float = 0.0  # ここに設定されたスコアでAI Studio画面上でフィルタリングが可能

def create_event_response(result: FrameAnalyzerResult) -> StreamAnalyzeResponse:
    return StreamAnalyzeResponse(
        record_event=StreamAnalyzeResponse.RecordEvent(
            timestamp=result.timestamp,
            type="detect.keyframe",
            event_index=str(result.timestamp.ToMilliseconds()),
            labels=result.labels,
            score=result.score,
            data=ParseDict(
                result.data,
                Struct(),
            ),
            geometry_config_ids=[1, 2, 3],
            picture=EventPicture(content_type="image/jpeg", data=result.thumbnail_data),
        )
    )

def create_object_response(result: FrameAnalyzerResult) -> StreamAnalyzeResponse:
    return StreamAnalyzeResponse(
        record_object=StreamAnalyzeResponse.RecordObject(
            start_timestamp=result.timestamp,
            end_timestamp=result.timestamp,
            type="detect.keyframe",
            object_index=str(result.timestamp.ToMilliseconds()),
            labels=result.labels,
            score=result.score,
            data=ParseDict(
                result.data,
                Struct(),
            ),
            geometry_config_ids=[1, 2, 3],
            picture=[
                ObjectPicture(
                    label=result.labels[0] if result.labels else "keyframe",
                    content_type="image/jpeg",
                    data=result.thumbnail_data,
                )
            ],
        )
    )


def create_metrics_response(result: FrameAnalyzerResult) -> StreamAnalyzeResponse:
    return StreamAnalyzeResponse(
        record_metrics=StreamAnalyzeResponse.RecordMetrics(
            timestamp=result.timestamp,
            units=["5minutes", "hourly", "daily"],
            metrics={
                "person": 1 if result.is_keyframe else 0,
                "random": random.random(),
            },
            daily_boundary_timezone="Asia/Tokyo",
        )
    )

def output_log():
    global log_file_name    
    with open(log_file_name, "w") as o:
        print(Logger().output(), file=o)

# `StreamAnalyzerService` を実装するクラス
class _StreamAnalyzer(StreamAnalyzerServiceServicer):

    # 動画ストリーム解析を行う
    def AnalyzeStream(self, it, ctx):
        global stream_count
        stream_id = stream_count 
        stream_count += 1
        print("connected !!!! : stream " + str(stream_id))
        log_id = Logger().start("AnalyzeStream", memo=f"stream_{stream_id}")

        # H.264ストリームのデコーダーを作成
        vcodec = av.CodecContext.create("h264", "r")

        logging.info("accept %s", ctx.peer())

        metadata = dict(ctx.invocation_metadata())
        request_id = metadata.get("request_id")
        device_id = metadata.get("device_id")

        # ユーザーおよびディベロッパーが指定したパラメータ情報を取得
        parameters = metadata.get("parameter")

        # コンテキスト情報を取得
        context = metadata.get("context")

        logging.info(
            "Start AnalyzeStream request_id=%s device_id=%s parameters=%s context=%s",
            request_id,
            device_id,
            parameters,
            context,
        )

        # configの読み込み
        parameters = json.loads(parameters)
        user_config = parameters["user_config"]

        start_pts = 0
        process_frame_time_ms = 0
        result = []
        result_file_name = f"result_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        analyzer = StreamAnalyzer()
        analyzer.open()

        ctx.send_initial_metadata((("analyzer_version", "v0.1.0"),))
        count = 0
        key_frame_count = 0
        logging.info("Start processing stream...")

        try:
            for r in it:
                # logging.info("Received media frame: %s", r.media_frame)
                # media_frame.type
                #
                # | byte | bit |
                # |------|-----|-------
                # |  3~1 |     | 未使用
                # |    0 |   7 | 0: 非キーフレーム, 1: キーフレーム
                # |    0 | 6~0 | 0: H264パケット, 1: AACパケット

                # 動画パケット(H264) 以外はスキップ
                if (r.media_frame.type & 0x01) != 0:
                    continue

                # 動画フレームのデコード
                p = av.Packet(r.media_frame.data)
                p.pts = r.media_frame.pts
                p.dts = r.media_frame.dts

                # パケットをデコードしてフレームを取得
                try:
                    decoded_frames = vcodec.decode(p)
                    # print('Decoded frames:', len(decoded_frames))
                    for decoded_frame in decoded_frames:
                        if decoded_frame is None:
                            continue
                        count += 1

                        try:
                            print('Decoded frame:', decoded_frame)

                            # デバッグ用にフレームを画像として保存
                            # if count % 30 == 0:
                            #     tm = Timestamp()
                            #     tm.FromDatetime(dt=datetime.datetime.fromtimestamp(p.pts / 90000, tz=datetime.timezone.utc))
                            #     pil_image = decoded_frame.to_image()
                            #     frame_rgb = np.array(pil_image.convert("RGB"))
                            #     cv2.imwrite(f"frame_{tm.seconds}_{tm.nanos}.jpg", cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))

                            tm = Timestamp()
                            tm.FromDatetime(dt=datetime.datetime.fromtimestamp(p.pts / 90000, tz=datetime.timezone.utc))

                            if start_pts == 0:
                                start_pts = p.pts
                            frame_timestamp = p.pts - start_pts
                            time_ms = int(frame_timestamp / 90)  # 90000Hz -> milliseconds                            
                            if time_ms - process_frame_time_ms < PROCESSING_INTERVAL_MS:
                                print('Skipping frame at timestamp:', time_ms)
                                continue
                            process_frame_time_ms = time_ms
                            print('Frame timestamp:', frame_timestamp, 'seconds:', frame_timestamp / 90000)

                            # to_image
                            decode_log_id = Logger().start("decode", memo=f"stream_{stream_id}")
                            pil_image = decoded_frame.to_image()
                            frame_rgb = np.array(pil_image.convert("RGB"))                            
                            Logger().stop(decode_log_id, memo=f"stream_{stream_id}")

                            # analyze
                            analyze_log_id = Logger().start("analyze", memo=f"stream_{stream_id}")
                            analyzer.analyze(frame_rgb, time_ms)
                            Logger().stop(analyze_log_id, memo=f"stream_{stream_id}")

                            # pop event
                            event = analyzer.pop_event()
                            if event:
                                event_data = event["data"]
                                data = {
                                    "event_index": event_data["event_index"],
                                    "type": event_data["type"],
                                    "labels": event_data["labels"],
                                    "geometry_config_ids": event_data["geometry_config_ids"],
                                    "data": event_data["data"],
                                }
                                print("Detected event:", data)
                                result.append({
                                    "time_ms": event["time_ms"],
                                    "data": {
                                        "event_index": event_data["event_index"],
                                        "type": event_data["type"],
                                        "labels": event_data["labels"],
                                        "geometry_config_ids": event_data["geometry_config_ids"],
                                        "data": event_data["data"],
                                    },
                                })
                                yield create_event_response(FrameAnalyzerResult(
                                    is_keyframe=decoded_frame.key_frame,
                                    timestamp=tm,
                                    data=data,
                                    labels=data["labels"],
                                    score=1.0,
                                ))

                            # TODO: pop object, pop metrics も同様に処理する場合はここに追加

                        except Exception as e:
                            logging.error("Failed to process frame: %s", str(e))
                            continue

                except av.error.InvalidDataError:
                    continue

        except Exception:
            logging.exception("abort")
            analyzer.close()
            Logger().stop(log_id, memo=f"stream_{stream_id}")
            output_log()
            json.dump(result, open(result_file_name, "w"), indent=2)
            raise

        else:
            logging.info("close")
            analyzer.close()
            Logger().stop(log_id, memo=f"stream_{stream_id}")
            output_log()
            json.dump(result, open(result_file_name, "w"), indent=2)

@click.command()
@click.option("--address", default="[::]:50051")
def serve(address: str) -> None:
    """Safie AIソリューションプラットフォームのストリームAnalyzerを起動します。"""
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(2))
    add_StreamAnalyzerServiceServicer_to_server(_StreamAnalyzer(), server)
    server.add_insecure_port(address)
    server.start()
    logging.info("server listening at %s", address)
    server.wait_for_termination()

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)
        server_log_id = Logger().start("server", memo="server") 
        serve()
    except Exception:
        logging.exception("abort")
    finally:
        Logger().stop(server_log_id, memo="server")
        output_log()