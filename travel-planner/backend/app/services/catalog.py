"""Curated fallback POIs used when an AMap server key is not configured.

The production adapter replaces this pool with AMap Place Search responses. Keeping a
small, licensed in-repo fallback makes local demos deterministic and lets the planner
be tested without a network/API key.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from app.models import Location


@dataclass(frozen=True)
class CandidatePoi:
    id: str
    name: str
    type: str
    categories: tuple[str, ...]
    location: Location
    visit_minutes: int
    opening_hours: str
    tips: str
    score: float = 4.5
    fee: int = 0
    closed_weekdays: frozenset[int] = frozenset()
    accessible: bool = True


def poi(
    id: str, name: str, type: str, categories: tuple[str, ...], lng: float, lat: float,
    minutes: int, hours: str, tips: str, *, score: float = 4.5, fee: int = 0,
    closed: tuple[int, ...] = (), accessible: bool = True,
) -> CandidatePoi:
    return CandidatePoi(
        id=id, name=name, type=type, categories=categories,
        location=Location(lng=lng, lat=lat), visit_minutes=minutes,
        opening_hours=hours, tips=tips, score=score, fee=fee,
        closed_weekdays=frozenset(closed), accessible=accessible,
    )


HANGZHOU: tuple[CandidatePoi, ...] = (
    poi('B000A8UIN8', '断桥残雪', '自然风光', ('natural', 'trending'), 120.1500, 30.2600, 45, '全天开放', '建议清晨前往，桥东侧光线更适合拍照。', score=4.9),
    poi('HZ-BAIDI', '白堤', '自然风光', ('natural', 'outdoor'), 120.1433, 30.2509, 60, '全天开放', '慢行优先，沿途有多处观湖停靠点。', score=4.8),
    poi('HZ-PHQY', '平湖秋月', '网红打卡', ('natural', 'trending'), 120.1367, 30.2482, 40, '全天开放', '11 点前后湖面较平，适合取景。', score=4.7),
    poi('HZ-LOUWAILOU', '楼外楼', '美食探店', ('food', 'culture'), 120.1304, 30.2382, 75, '10:30-20:00', '建议提前取号，西湖醋鱼与龙井虾仁很受欢迎。', score=4.6, fee=180),
    poi('HZ-QYFH', '曲院风荷', '自然风光', ('natural', 'trending'), 120.1248, 30.2316, 75, '全天开放', '夏季荷花盛放，雨后木栈道较滑。', score=4.8),
    poi('HZ-SD', '苏堤春晓', '自然风光', ('natural', 'outdoor'), 120.1192, 30.2216, 60, '全天开放', '建议从北向南游览，傍晚光线最柔和。', score=4.8),
    poi('HZ-LINGYIN', '灵隐寺', '宗教寺庙', ('temple', 'culture'), 120.1013, 30.2338, 90, '07:30-18:15', '请提前预约；入寺着装宜得体。', score=4.9, fee=75),
    poi('HZ-FLYF', '飞来峰', '历史人文', ('culture', 'outdoor', 'temple'), 120.1001, 30.2303, 75, '07:30-17:30', '石窟光线偏暗，拍摄可开启夜景模式。', score=4.8, fee=45, accessible=False),
    poi('HZ-FAXI', '法喜寺', '宗教寺庙', ('temple', 'trending'), 120.0869, 30.1992, 70, '06:30-18:00', '午后人流相对平稳，山路需慢行。', score=4.7, fee=10),
    poi('HZ-LONGJING', '龙井村', '户外运动', ('outdoor', 'natural', 'food'), 120.0952, 30.1882, 100, '全天开放', '如购茶请认准正规门店，山路会车需慢行。', score=4.7, accessible=False),
    poi('HZ-TEA-MUSEUM', '中国茶叶博物馆', '博物馆', ('museum', 'culture'), 120.1060, 30.1941, 80, '09:00-17:00', '周一部分展厅闭馆，建议确认预约时段。', score=4.7, closed=(0,)),
    poi('HZ-MAOJIABU', '茅家埠', '自然风光', ('natural', 'outdoor'), 120.1120, 30.2172, 70, '全天开放', '水杉与湿地景观安静，适合预留半小时散步。', score=4.6),
    poi('HZ-GONGCHEN', '拱宸桥', '历史人文', ('culture', 'trending'), 120.1498, 30.3133, 45, '全天开放', '建议从西岸开始步行，桥面晨光很好。', score=4.7),
    poi('HZ-CANAL-MUSEUM', '中国京杭大运河博物馆', '博物馆', ('museum', 'culture'), 120.1509, 30.3090, 100, '09:00-16:30', '建议预约讲解，馆外咖啡店适合午间休息。', score=4.7, closed=(0,)),
    poi('HZ-XIAOHE', '小河直街历史文化街区', '历史人文', ('culture', 'food', 'trending'), 120.1446, 30.3068, 75, '全天开放', '沿河小店适合简餐，避开正午排队。', score=4.7),
    poi('HZ-QIAOXI', '桥西历史街区', '网红打卡', ('trending', 'culture', 'shopping'), 120.1434, 30.3161, 80, '全天开放', '老厂房与运河景观适合慢慢逛。', score=4.6),
    poi('HZ-XIANGJI', '香积寺', '宗教寺庙', ('temple', 'culture'), 120.1533, 30.3208, 65, '08:00-17:00', '17 点前入内更从容，寺外有运河夜景。', score=4.6, fee=20),
    poi('HZ-HUBIN', '湖滨步行街', '购物商圈', ('shopping', 'food', 'trending'), 120.1650, 30.2520, 100, '10:00-22:00', '傍晚亮灯后适合逛街，周末停车紧张。', score=4.6),
    poi('HZ-ZHONGSHAN', '南宋御街', '历史人文', ('culture', 'food', 'shopping'), 120.1694, 30.2411, 75, '全天开放', '从鼓楼方向进入，人流相对均衡。', score=4.5),
)

SHANGHAI: tuple[CandidatePoi, ...] = (
    poi('SH-WAITAN', '外滩', '网红打卡', ('trending', 'culture'), 121.4900, 31.2410, 70, '全天开放', '傍晚至夜间亮灯，江风较大请备外套。', score=4.9),
    poi('SH-NANJING', '南京路步行街', '购物商圈', ('shopping', 'food', 'trending'), 121.4755, 31.2387, 90, '全天开放', '可避开周末午后高峰，步行街全程禁行车辆。', score=4.6),
    poi('SH-YUYUAN', '豫园', '历史人文', ('culture', 'food', 'trending'), 121.4928, 31.2273, 100, '09:00-16:30', '建议提前预约，九曲桥午后较拥挤。', score=4.7, fee=40),
    poi('SH-XINTIANDI', '新天地', '美食探店', ('food', 'shopping', 'trending'), 121.4758, 31.2191, 100, '10:00-23:00', '石库门街区适合晚餐与夜间散步。', score=4.6),
    poi('SH-MUSEUM', '上海博物馆', '博物馆', ('museum', 'culture'), 121.4754, 31.2302, 140, '09:00-17:00', '需预约入馆，建议优先看青铜与书画展厅。', score=4.8, closed=(0,)),
    poi('SH-WUKANG', '武康路', '网红打卡', ('trending', 'culture', 'outdoor'), 121.4402, 31.2032, 75, '全天开放', '住宅区请轻声慢行，建筑外立面适合晨拍。', score=4.7),
    poi('SH-ART', '西岸艺术中心', '博物馆', ('museum', 'trending'), 121.4535, 31.1778, 110, '10:00-17:00', '展览以当期安排为准，江边适合骑行。', score=4.5, closed=(0,)),
    poi('SH-DISNEY', '上海迪士尼乐园', '主题乐园', ('themePark', 'family'), 121.6577, 31.1434, 330, '08:30-21:30', '建议单独安排全天，并提前预约热门项目。', score=4.9, fee=719),
)

BEIJING: tuple[CandidatePoi, ...] = (
    poi('BJ-GUGONG', '故宫博物院', '博物馆', ('museum', 'culture', 'trending'), 116.3970, 39.9180, 180, '08:30-16:30', '必须提前预约；建议午门进、神武门出。', score=4.9, fee=60, closed=(0,)),
    poi('BJ-JINGSHAN', '景山公园', '自然风光', ('natural', 'culture', 'outdoor'), 116.3976, 39.9241, 65, '06:30-21:00', '万春亭可俯瞰中轴线，台阶较多。', score=4.8, fee=2, accessible=False),
    poi('BJ-BEIHHAI', '北海公园', '自然风光', ('natural', 'culture'), 116.3836, 39.9249, 100, '06:30-20:00', '建议从北门或东门进入，避开团客入口。', score=4.7, fee=10),
    poi('BJ-SHICHAHAI', '什刹海', '历史人文', ('culture', 'food', 'trending'), 116.3855, 39.9415, 95, '全天开放', '傍晚沿湖漫步，酒吧街适合晚间。', score=4.7),
    poi('BJ-NANLUO', '南锣鼓巷', '美食探店', ('food', 'shopping', 'trending'), 116.4038, 39.9372, 80, '10:00-22:00', '建议从北向南走，避开午后主街拥堵。', score=4.5),
    poi('BJ-TEMPLE', '天坛公园', '历史人文', ('culture', 'natural', 'trending'), 116.4074, 39.8822, 130, '06:30-22:00', '祈年殿建议上午参观，拍照光线更柔和。', score=4.8, fee=34),
    poi('BJ-798', '798艺术区', '网红打卡', ('trending', 'museum', 'shopping'), 116.4948, 39.9840, 120, '10:00-18:00', '展馆开闭时间不同，周一部分店铺休息。', score=4.6),
    poi('BJ-SUMMER', '颐和园', '自然风光', ('natural', 'culture', 'outdoor'), 116.2740, 39.9997, 180, '06:30-20:00', '面积较大，建议独立安排半天以上。', score=4.9, fee=30),
)

SUZHOU: tuple[CandidatePoi, ...] = (
    poi('SZ-ZHUOZHENG', '拙政园', '历史人文', ('culture', 'trending'), 120.6257, 31.3262, 120, '07:30-17:30', '建议开园即入，避开旅行团高峰。', score=4.9, fee=80),
    poi('SZ-PINGJIANG', '平江路历史街区', '历史人文', ('culture', 'food', 'trending'), 120.6320, 31.3180, 100, '全天开放', '沿河慢逛，评弹茶馆可提前预约。', score=4.8),
    poi('SZ-SHIZILIN', '狮子林', '历史人文', ('culture', 'trending'), 120.6266, 31.3294, 80, '07:30-17:30', '假山路径狭窄，儿童需留意脚下。', score=4.7, fee=40, accessible=False),
    poi('SZ-SUZHOU-MUSEUM', '苏州博物馆', '博物馆', ('museum', 'culture', 'trending'), 120.6275, 31.3272, 120, '09:00-17:00', '建筑本身值得细看，需提前预约。', score=4.9, closed=(0,)),
    poi('SZ-SHANTANG', '山塘街', '美食探店', ('food', 'culture', 'trending'), 120.6104, 31.3268, 90, '全天开放', '夜景较美，坐船项目请留意末班时间。', score=4.7),
    poi('SZ-JINJI', '金鸡湖', '自然风光', ('natural', 'shopping', 'trending'), 120.7203, 31.3199, 120, '全天开放', '适合傍晚骑行，周边商场餐饮丰富。', score=4.6),
)

CITY_POOLS: dict[str, tuple[CandidatePoi, ...]] = {
    '杭州': HANGZHOU, '杭州西湖': HANGZHOU,
    '上海': SHANGHAI,
    '北京': BEIJING,
    '苏州': SUZHOU,
}


def catalog_for_destination(destination: str) -> tuple[CandidatePoi, ...]:
    """Return the closest supported offline catalog; Hangzhou is the rich demo pool."""
    normalized = destination.replace('市', '').replace('区', '').strip()
    for key, pool in CITY_POOLS.items():
        if key in normalized or normalized in key:
            return pool
    return HANGZHOU


def rank_candidates(
    candidates: Iterable[CandidatePoi], preferences: Iterable[str], *,
    budget_max: float | None = None, needs_accessible: bool = False,
    special_needs: str | None = None,
) -> list[CandidatePoi]:
    preference_set = set(preferences)
    special = (special_needs or '').lower()
    ranked: list[tuple[float, CandidatePoi]] = []
    for item in candidates:
        if needs_accessible and not item.accessible:
            continue
        if budget_max is not None and item.fee > budget_max:
            continue
        if ('宠物' in special or 'pet' in special) and item.type in {'博物馆', '宗教寺庙'}:
            continue
        match_bonus = 0.65 * len(preference_set.intersection(item.categories))
        # Keep a small amount of diversity rather than making all POIs the same type.
        score = item.score + match_bonus + (0.08 if item.fee == 0 else 0)
        ranked.append((score, item))
    ranked.sort(key=lambda pair: (-pair[0], pair[1].name))
    return [item for _, item in ranked]


def with_location(item: CandidatePoi, location: Location) -> CandidatePoi:
    return replace(item, location=location)
