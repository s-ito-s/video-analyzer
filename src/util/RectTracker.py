from dataclasses import dataclass

@dataclass
class TrackedRect:
    """追跡中の矩形オブジェクト"""
    id: int
    x: int
    y: int
    w: int
    h: int
    lost_count: int = 0  # 検出されなかったフレーム数
    hit_count: int = 1   # 連続検出フレーム数
    confirmed: bool = False  # 確定済みかどうか

class RectTracker:
    """動画フレーム内の矩形領域を追跡するクラス。

    フレームごとに検出された矩形リストを受け取り、
    前フレームの矩形とIoU(重なり率)で対応付けを行う。
    新規出現・消失したオブジェクトを判定して返す。

    Args:
        iou_threshold: 同一物体とみなすIoUの閾値 (0.0〜1.0)
        max_lost_frames: 未検出のまま保持する最大フレーム数
        min_confirm_frames: 確定に必要な連続検出フレーム数。
            この数未満で消失した検出は誤検出として破棄する。
    """

    def __init__(self, iou_threshold: float = 0.8, max_lost_frames: int = 3,
                 min_confirm_frames: int = 3):
        self._iou_threshold = iou_threshold
        self._max_lost_frames = max_lost_frames
        self._min_confirm_frames = max(1, min_confirm_frames)
        self._next_id = 0
        self._tracked: dict[int, TrackedRect] = {}

    @property
    def tracked_objects(self) -> dict[int, TrackedRect]:
        """現在追跡中のオブジェクト(消失待ちも含む)"""
        return dict(self._tracked)

    @property
    def active_objects(self) -> dict[int, TrackedRect]:
        """現在検出中かつ確定済み(confirmed)のオブジェクトのみ"""
        return {k: v for k, v in self._tracked.items()
                if v.lost_count == 0 and v.confirmed}

    def update(self, rects: list[tuple[int, int, int, int]]) -> tuple[list[TrackedRect], list[TrackedRect]]:
        """検出矩形リストで追跡状態を更新する。

        Args:
            rects: 検出された矩形のリスト。各要素は (x, y, w, h)。

        Returns:
            (appeared, disappeared) のタプル。
            appeared: 今回新たに出現したオブジェクトのリスト。
            disappeared: 今回消失と判定されたオブジェクトのリスト。
        """
        appeared: list[TrackedRect] = []
        disappeared: list[TrackedRect] = []

        # 既存オブジェクトとのIoUマッチング
        matched_track_ids: set[int] = set()
        matched_rect_indices: set[int] = set()

        # IoU行列を計算してスコアの高い順に貪欲マッチング
        pairs: list[tuple[float, int, int]] = []
        for track_id, tracked in self._tracked.items():
            for i, rect in enumerate(rects):
                iou = self._calc_iou(
                    (tracked.x, tracked.y, tracked.w, tracked.h), rect
                )
                if iou >= self._iou_threshold:
                    pairs.append((iou, track_id, i))

        pairs.sort(key=lambda p: p[0], reverse=True)

        for iou, track_id, rect_idx in pairs:
            if track_id in matched_track_ids or rect_idx in matched_rect_indices:
                continue
            # 既存オブジェクトの位置を更新
            x, y, w, h = rects[rect_idx]
            tracked_obj = self._tracked[track_id]
            tracked_obj.x = x
            tracked_obj.y = y
            tracked_obj.w = w
            tracked_obj.h = h
            tracked_obj.lost_count = 0
            tracked_obj.hit_count += 1
            # 連続検出が閾値に達した瞬間に確定 → appeared に追加
            if not tracked_obj.confirmed and tracked_obj.hit_count >= self._min_confirm_frames:
                tracked_obj.confirmed = True
                appeared.append(tracked_obj)
            matched_track_ids.add(track_id)
            matched_rect_indices.add(rect_idx)

        # マッチしなかった既存オブジェクト → lost_count 増加 or 消失
        for track_id in list(self._tracked.keys()):
            if track_id in matched_track_ids:
                continue
            tracked_obj = self._tracked[track_id]
            tracked_obj.lost_count += 1
            tracked_obj.hit_count = 0  # 連続検出カウントをリセット
            if tracked_obj.lost_count > self._max_lost_frames:
                removed = self._tracked.pop(track_id)
                if removed.confirmed:
                    # 確定済みオブジェクトのみ消失として報告
                    disappeared.append(removed)
                # 未確定のものは誤検出として静かに破棄

        # マッチしなかった検出矩形 → 新規オブジェクト(仮登録)
        for i, rect in enumerate(rects):
            if i in matched_rect_indices:
                continue
            x, y, w, h = rect
            is_confirmed = self._min_confirm_frames <= 1
            new_obj = TrackedRect(
                id=self._next_id, x=x, y=y, w=w, h=h,
                confirmed=is_confirmed,
            )
            self._tracked[self._next_id] = new_obj
            if is_confirmed:
                appeared.append(new_obj)
            self._next_id += 1

        return { 'appeared':appeared, 'disappeared':disappeared }

    def reset(self):
        """追跡状態をすべてクリアする。"""
        self._tracked.clear()
        self._next_id = 0

    @staticmethod
    def _calc_iou(
        rect_a: tuple[int, int, int, int],
        rect_b: tuple[int, int, int, int],
    ) -> float:
        """2つの矩形 (x, y, w, h) のIoUを計算する。"""
        ax, ay, aw, ah = rect_a
        bx, by, bw, bh = rect_b

        inter_x1 = max(ax, bx)
        inter_y1 = max(ay, by)
        inter_x2 = min(ax + aw, bx + bw)
        inter_y2 = min(ay + ah, by + bh)

        inter_w = max(0, inter_x2 - inter_x1)
        inter_h = max(0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h

        area_a = aw * ah
        area_b = bw * bh
        union_area = area_a + area_b - inter_area

        if union_area == 0:
            return 0.0
        return inter_area / union_area
