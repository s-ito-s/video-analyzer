import json
import logging
import os.path
import subprocess
import tempfile
import time
from datetime import datetime
import tkinter.filedialog

import av
import av.datasets
import click
import grpc
from google.protobuf.json_format import MessageToDict

from proto.stream.v1.analyzer_pb2 import StreamAnalyzeRequest
from proto.stream.v1.analyzer_pb2_grpc import StreamAnalyzerServiceStub
# from tools.validator import (
#     validate_context,
#     validate_device_status,
#     validate_event,
#     validate_metrics,
#     validate_object,
# )

from log.logger import Logger
log_file_name = f"client_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


@click.command()
@click.option(
    "--in-filename", type=click.Path(readable=True), default=None, help="Path to input mp4 video file"
)
@click.option(
    "--user-config", "-u", type=click.Path(readable=True), default=None, help="Path to user_config JSON file"
)
@click.option(
    "--developer-config",
    "-d",
    type=click.Path(readable=True),
    default=None,
    help="Path to developer_config JSON file",
)
@click.option(
    "--geometry-config",
    "-g",
    type=click.Path(readable=True),
    default=None,
    help="Path to geometry_config JSON file",
)
@click.option(
    "--context", "-c", type=click.Path(readable=True), default=None, help="Path to context JSON file"
)
@click.option(
    "--base-timestamp",
    "-t",
    type=str,
    default=None,
    help=(
        "base timestamp of the video stream. current timestamp is used by default. "
        "RFC3339 date-time format is supported."
    ),
)
@click.option("--address", default="localhost:50051")
@click.option("-re", is_flag=True, default=False, help="emulate source framerate")
def client(in_filename, user_config, developer_config, geometry_config, context, base_timestamp, address, re):
    """Safie AIソリューションプラットフォームのストリームAnalyzerに対して指定された動画データを送信します。
    ファイルはひとつのH.264動画ストリームおよび任意のAAC音声ストリームから構成される必要があります。
    """

    # 指定がない場合サンプル動画ファイルを使用
    if in_filename is None:
        in_filename = tkinter.filedialog.askopenfilename()
    print("Input file: ", in_filename)

    # パラメータ情報の生成
    user_config_dict = {}
    if user_config is not None:
        with open(user_config, "r") as f:
            user_config_dict = json.loads(f.read())

    developer_config_dict = {}
    if developer_config is not None:
        with open(developer_config, "r") as f:
            developer_config_dict = json.loads(f.read())

    geometry_config_list = []
    if geometry_config is not None:
        with open(geometry_config, "r") as f:
            geometry_config_list = json.loads(f.read())

    if geometry_config_list:
        user_config_dict["geometries"] = geometry_config_list

    parameter = {}
    parameter["user_config"] = user_config_dict
    parameter["developer_config"] = developer_config_dict

    context_dict = {}
    if context is not None:
        with open(context, "r") as f:
            context_dict = json.loads(f.read())

    # 動画ファイルからパケットを取得
    def read_packets():
        with av.open(in_filename) as c:
            for p in c.demux():
                if p.dts is None:
                    return
                yield p

    # 動画ファイルからH.264パケット (H.264 Annex.B, Byte Stream Format形式) を取得
    # NOTE: pyavは現在のところFFmpeg bitstream filterに非対応
    def read_annexb_packets():
        with tempfile.TemporaryDirectory() as dir:
            h264_file = os.path.join(dir, "in.h264")
            subprocess.check_call(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    in_filename,
                    "-vcodec",
                    "copy",
                    "-an",
                    "-bsf:v",
                    "h264_mp4toannexb",
                    h264_file,
                ]
            )

            with open(h264_file, "rb") as fp:
                codec = av.CodecContext.create("h264", "r")
                while True:
                    chunk = fp.read(4 * 1024)
                    for p in codec.parse(chunk):
                        yield p
                    if not chunk:
                        break

    # サーバーに送信するパケットを生成する
    def it():
        packets = read_packets()
        annexb_packets = read_annexb_packets()

        # pts/dtsを現在時刻で補正
        t = int(time.time() * 90000)
        if base_timestamp:
            # RFC3339形式のtimestampを取得
            t = int(datetime.fromisoformat(base_timestamp).timestamp() * 90000)

        for p in packets:
            p2 = None
            if p.stream.type == "video":
                # 動画フレームをAnnex.B形式で置き換える
                p2 = next(annexb_packets)
                type_ = 0x80 if p.is_keyframe else 0x00
            elif p.stream.type == "audio":
                type_ = 0x01
            else:
                continue

            if (p.stream.type == "video"):
                print('Read packet:', (p.pts / 90000), p.pts, p.dts, p.stream.type)

            # Requestを送信
            request_log_id = Logger().start("request", memo=f"packet_{p.pts}")
            yield StreamAnalyzeRequest(
                media_frame=StreamAnalyzeRequest.MediaFrame(                 
                    pts=(p.pts + t) % 2**64,
                    dts=(p.dts + t) % 2**64,
                    type=type_,
                    data=bytes(p2) if p2 else bytes(p),
                ),
            )
            Logger().stop(request_log_id, memo=f"packet_{p.pts}")

            # `-re` オプションが指定されたときディレイを入れる
            wait = (float(t + p.dts) / 90000) - time.time()
            if wait > 0 and p.stream.type == "video":
                print('Waiting for %.2f mill seconds to emulate source framerate...' % (wait * 1000))
                time.sleep(wait)

        next(annexb_packets, None)

    # gRPC接続
    with grpc.insecure_channel(address) as channel:
        logging.info("Connected")
        metadata = [
            ("request_id", "sample-request"),
            ("device_id", "sample-device"),
            ("stream.video_type", "H264"),
            ("stream.video_width", "1280"),
            ("stream.video_height", "720"),
            ("stream.video_framerate", "30"),
            ("stream.audio_type", "AAC"),
            ("stream.audio_samplebits", "8"),
            ("stream.audio_samplerate", "48000"),
            ("stream.audio_channels", "1"),
            ("context", json.dumps(context_dict) if context_dict else ""),
            ("parameter", json.dumps(parameter)),
        ]

        try:
            stub = StreamAnalyzerServiceStub(channel)
            print("Sending stream")

            # パケットを送信
            r_it = stub.AnalyzeStream(it(), metadata=metadata)
            logging.info("Initial metadata: %s", r_it.initial_metadata())

            for r in r_it:
                print(r)
                # レスポンスの処理
                # if r.HasField("record_metrics"):
                #     metrics = validate_metrics(
                #         MessageToDict(r.record_metrics, preserving_proto_field_name=True)
                #     )
                #     logging.info("  metrics: %s", [m.model_dump() for m in metrics])

                # elif r.HasField("record_event"):
                #     event = validate_event(MessageToDict(r.record_event, preserving_proto_field_name=True))
                #     logging.info("  event: %s", event.model_dump())

                # elif r.HasField("record_object"):
                #     object = validate_object(MessageToDict(r.record_object, preserving_proto_field_name=True))
                #     logging.info("  object: %s", object.model_dump())

                # elif r.HasField("record_device_status"):
                #     device_status = validate_device_status(
                #         MessageToDict(r.record_device_status, preserving_proto_field_name=True)
                #     )
                #     logging.info(
                #         "  device status: %s",
                #         [d.model_dump() for d in device_status],
                #     )
                # elif r.HasField("update_context"):
                #     validate_context(r.update_context)
                #     logging.info(
                #         "  update context: %s",
                #         MessageToDict(r.update_context, preserving_proto_field_name=True),
                #     )

        except Exception:
            logging.exception("Aborted")
            Logger().stop(log_client_id, memo="client")
            output_log()
            raise
        else:
            logging.info("Closed")
            Logger().stop(log_client_id, memo="client")
            output_log()

def output_log():
    global log_file_name
    with open(log_file_name, "w") as o:
        print(Logger().output(), file=o)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    log_client_id = Logger().start("client", memo="client")
    try:
        client()
    except Exception:
        logging.exception("Client error")
    finally:
        Logger().stop(log_client_id, memo="client")
        output_log()

