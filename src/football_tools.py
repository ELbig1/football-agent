"""
Football Tools
================
كل حاجة خاصة بأدوات الكورة موجودة هنا: تعريف الأدوات (TOOLS)
وتنفيذها الفعلي (execute_*).

الأدوات الأربعة:
  1) calculate_standings -> حاسبة نقاط/ترتيب (محليًا، من غير إنترنت)
  2) days_until_match     -> حاسبة أيام (محليًا، من غير إنترنت)
  3) get_next_match        -> أقرب مباراة قادمة لفريق (من TheSportsDB)
  4) get_match_result      -> آخر نتيجة فعلية لفريق (من TheSportsDB)

TheSportsDB API مجاني تمامًا ومفيهوش تسجيل - بيستخدم مفتاح تجريبي
عام اسمه '123' (موثّق رسميًا من الموقع نفسه للاستخدام التجريبي).
"""

import os
import requests
from datetime import datetime, date

# مفتاح TheSportsDB التجريبي العام - شغال من غير تسجيل خالص.
# لو حبيت مفتاح شخصي بعدين (حد أعلى للطلبات)، حطه في .env باسم
# THESPORTSDB_API_KEY وهيتستخدم تلقائيًا بدل التجريبي.
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "123")
THESPORTSDB_BASE = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_standings",
            "description": (
                "احسب نقاط وفارق أهداف فريق (أو أكتر) من نتايج مباريات "
                "بصيغة فوز/تعادل/خسارة وأهداف له وعليه. استخدمها لما "
                "المستخدم يديك نتايج مباريات وعايز تحسبله الترتيب أو "
                "النقاط أو فارق الأهداف."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "teams": {
                        "type": "array",
                        "description": "قائمة بالفرق ونتايجهم",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "اسم الفريق"},
                                "wins": {"type": "integer", "description": "عدد مرات الفوز"},
                                "draws": {"type": "integer", "description": "عدد مرات التعادل"},
                                "losses": {"type": "integer", "description": "عدد مرات الخسارة"},
                                "goals_for": {"type": "integer", "description": "عدد الأهداف المسجلة له"},
                                "goals_against": {"type": "integer", "description": "عدد الأهداف المسجلة عليه"},
                            },
                            "required": ["name", "wins", "draws", "losses"],
                        },
                    }
                },
                "required": ["teams"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "days_until_match",
            "description": (
                "احسب كام يوم باقي (أو فات) على تاريخ مباراة معينة، "
                "بمقارنته بتاريخ النهاردة. استخدمها لما يكون التاريخ "
                "معروف بالفعل (مذكور في السؤال أو جاي من أداة تانية)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "match_date": {
                        "type": "string",
                        "description": "تاريخ المباراة بصيغة YYYY-MM-DD",
                    }
                },
                "required": ["match_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_next_match",
            "description": (
                "هات أقرب مباراة قادمة لفريق كورة معين (تاريخها، الخصم، "
                "والبطولة). استخدمها لما المستخدم يسأل عن مباراة فريق "
                "الجاية إمتى أو مين هيلعب ضد مين."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team_name": {
                        "type": "string",
                        "description": "اسم الفريق بالإنجليزي (زي Al Ahly أو Zamalek)",
                    }
                },
                "required": ["team_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_match_result",
            "description": (
                "هات آخر نتيجة فعلية لفريق كورة معين (النتيجة، الخصم، "
                "والتاريخ). استخدمها لما المستخدم يسأل عن آخر مباراة "
                "لعبها فريق أو نتيجتها كانت إيه."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team_name": {
                        "type": "string",
                        "description": "اسم الفريق بالإنجليزي (زي Al Ahly أو Zamalek)",
                    }
                },
                "required": ["team_name"],
            },
        },
    },
]


def _find_team_id(team_name: str) -> tuple[str, str] | None:
    """بيرجع (team_id, الاسم الرسمي) أو None لو الفريق مش موجود"""
    resp = requests.get(
        f"{THESPORTSDB_BASE}/searchteams.php",
        params={"t": team_name},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    teams = data.get("teams")
    if not teams:
        return None
    team = teams[0]  # أول نتيجة (أقرب تطابق)
    return team.get("idTeam"), team.get("strTeam")


# ---------------------------------------------------------
# تنفيذ الأدوات فعليًا
# ---------------------------------------------------------
def execute_calculate_standings(teams: list) -> str:
    print(f"   🧮 [Tool Call] Calculating standings for {len(teams)} team(s)")
    rows = []
    for t in teams:
        wins = t.get("wins", 0)
        draws = t.get("draws", 0)
        losses = t.get("losses", 0)
        goals_for = t.get("goals_for", 0)
        goals_against = t.get("goals_against", 0)

        points = wins * 3 + draws * 1
        goal_diff = goals_for - goals_against
        played = wins + draws + losses

        rows.append(
            {
                "name": t.get("name", "فريق"),
                "played": played,
                "points": points,
                "goal_diff": goal_diff,
                "goals_for": goals_for,
                "goals_against": goals_against,
            }
        )

    rows.sort(key=lambda r: (r["points"], r["goal_diff"]), reverse=True)

    lines = []
    for i, r in enumerate(rows, start=1):
        lines.append(
            f"{i}. {r['name']} - لعب {r['played']} | نقاط: {r['points']} "
            f"| فارق الأهداف: {r['goal_diff']:+d} (له {r['goals_for']} / عليه {r['goals_against']})"
        )
    return "\n".join(lines)


def execute_days_until_match(match_date: str) -> str:
    print(f"   📅 [Tool Call] Calculating days until: {match_date}")
    try:
        target = datetime.strptime(match_date, "%Y-%m-%d").date()
    except ValueError:
        return f"صيغة التاريخ غلط: '{match_date}'. المطلوب صيغة YYYY-MM-DD."

    today = date.today()
    diff = (target - today).days

    if diff > 0:
        return f"باقي {diff} يوم على {match_date} (النهاردة {today.isoformat()})."
    elif diff == 0:
        return f"المباراة النهاردة ({match_date})!"
    else:
        return f"المباراة فاتت من {abs(diff)} يوم ({match_date})."


def execute_get_next_match(team_name: str) -> str:
    print(f"   ⚽ [Tool Call] Getting next match for: '{team_name}'")
    try:
        found = _find_team_id(team_name)
        if not found:
            return f"مش لاقي فريق اسمه '{team_name}' في قاعدة البيانات."
        team_id, official_name = found

        resp = requests.get(
            f"{THESPORTSDB_BASE}/eventsnext.php",
            params={"id": team_id},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events")
        if not events:
            return f"مفيش مباريات قادمة معروفة لـ {official_name} حاليًا."

        e = events[0]
        return (
            f"{official_name}: المباراة الجاية {e.get('strEvent', '')} "
            f"في {e.get('dateEvent', 'تاريخ غير معروف')} "
            f"الساعة {e.get('strTime', 'غير محدد')} "
            f"({e.get('strLeague', '')})."
        )
    except requests.RequestException as e:
        return f"حصل خطأ في الاتصال بـ TheSportsDB: {e}"


def execute_get_match_result(team_name: str) -> str:
    print(f"   ⚽ [Tool Call] Getting last result for: '{team_name}'")
    try:
        found = _find_team_id(team_name)
        if not found:
            return f"مش لاقي فريق اسمه '{team_name}' في قاعدة البيانات."
        team_id, official_name = found

        resp = requests.get(
            f"{THESPORTSDB_BASE}/eventslast.php",
            params={"id": team_id},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        events = data.get("results") or data.get("events")
        if not events:
            return f"مفيش نتايج سابقة معروفة لـ {official_name} حاليًا."

        e = events[0]
        home = e.get("strHomeTeam", "؟")
        away = e.get("strAwayTeam", "؟")
        home_score = e.get("intHomeScore", "؟")
        away_score = e.get("intAwayScore", "؟")
        return (
            f"{official_name}: آخر نتيجة - {home} {home_score} - {away_score} {away} "
            f"بتاريخ {e.get('dateEvent', 'غير معروف')} ({e.get('strLeague', '')})."
        )
    except requests.RequestException as e:
        return f"حصل خطأ في الاتصال بـ TheSportsDB: {e}"


TOOL_EXECUTORS = {
    "calculate_standings": lambda args: execute_calculate_standings(args["teams"]),
    "days_until_match": lambda args: execute_days_until_match(args["match_date"]),
    "get_next_match": lambda args: execute_get_next_match(args["team_name"]),
    "get_match_result": lambda args: execute_get_match_result(args["team_name"]),
}