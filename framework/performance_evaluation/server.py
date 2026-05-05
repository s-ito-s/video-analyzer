import concurrent.futures
import datetime
import json
import logging

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
from StreamAnalyzer import StreamAnalyzer

import av
import click
import grpc
import numpy as np
from google.protobuf.timestamp_pb2 import Timestamp
from proto.stream.v1.analyzer_pb2_grpc import (
    StreamAnalyzerServiceServicer,
    add_StreamAnalyzerServiceServicer_to_server,
)

from log.logger import Logger

# デバッグ用
import cv2

stream_count = 0

def output_log():
    with open("server_log.csv", "w") as o:
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

        result = []
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

                            decode_log_id = Logger().start("decode", memo=f"stream_{stream_id}")
                            pil_image = decoded_frame.to_image()
                            frame_rgb = np.array(pil_image.convert("RGB"))                            
                            Logger().stop(decode_log_id, memo=f"stream_{stream_id}")
                            analyze_log_id = Logger().start("analyze", memo=f"stream_{stream_id}")
                            bboxes = analyzer.analyze(frame_rgb, tm)
                            Logger().stop(analyze_log_id, memo=f"stream_{stream_id}")

                            if len(bboxes) > 0:
                                result.append({
                                    "timestamp": tm.ToDatetime().isoformat(),
                                    "bboxes": bboxes,
                                })
                                # デバッグ用: 画像出力
                                # cv2.imwrite(f"frame_{tm.seconds}_{tm.nanos}.jpg", cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))

                            responses = []
                        except Exception as e:
                            logging.error("Failed to process frame: %s", str(e))
                            continue

                        for res in responses:
                            if res is not None:
                                yield res

                except av.error.InvalidDataError:
                    continue

        except Exception:
            logging.exception("abort")
            analyzer.close()
            Logger().stop(log_id, memo=f"stream_{stream_id}")
            output_log()
            json.dump(result, open("result.json", "w"), indent=2)
            raise

        else:
            logging.info("close")
            analyzer.close()
            Logger().stop(log_id, memo=f"stream_{stream_id}")
            output_log()
            json.dump(result, open("result.json", "w"), indent=2)

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