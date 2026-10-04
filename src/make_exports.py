"""
make_exports.py - D1 data: monthly HR exports for the fictional Vltava Market Group.

Simulates the workforce month by month (Sep 2024 - Oct 2026) and writes one CSV per
month-end, shaped like a SAP SuccessFactors Employee Central ad hoc report built on
"Job Information" fields. Then plants a known set of data-quality issues so the
Power Query rules in D1 have something real to catch, and writes an answer key.

Outputs
  data/exports/YYYY-MM.csv                         Sep 2024 - Sep 2026 (25 files)
  data/demo_dropin/2026-10.csv                     next month's file, for the refresh demo
  data/reference/planted_issues.csv                answer key for the data-quality rules
  data/reference/termination_reasons.csv           lookup: Event Reason -> leaver category
  data/reference/legal_entities.csv                lookup: legal entity -> country, currency
  data/ticket/hrbp_operations_list_2026-10-02.csv  the HRBP's own list in Ticket #4711

Everyone in these files is synthetic (Faker). Run from the repo root:
  python src/make_exports.py
"""

from __future__ import annotations

import calendar
import os
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
from faker import Faker

SEED = int(os.environ.get("VMG_SEED", 2043))  # override only to explore other random worlds
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

FIRST_MONTH = date(2024, 9, 1)
LAST_EXPORT_MONTH = date(2026, 9, 1)  # last file that goes into data/exports
DROPIN_MONTH = date(2026, 10, 1)  # simulated too, but saved separately for the demo
LEADERSHIP_CHANGE_MONTH = date(2026, 5, 1)
REORG_DATE = date(2026, 7, 1)

COLUMNS = [
    "Person ID External", "First Name", "Last Name", "Gender", "Employee Status",
    "Employee Class", "Hire Date", "Event", "Event Reason", "Event Date",
    "Regret Termination", "Division", "Department", "Cost Center", "Legal Entity",
    "Location", "Job Title", "Pay Grade", "FTE", "Manager ID", "Annual Salary", "Currency",
]

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

ENTITIES = {
    "DE": {"legal_entity": "VMG Deutschland GmbH", "location": "Frankfurt", "currency": "EUR", "pay_factor": 1.00, "locale": "de_DE"},
    "CZ": {"legal_entity": "VMG Czech Republic s.r.o.", "location": "Prague", "currency": "CZK", "pay_factor": 0.55, "locale": "cs_CZ"},
    "LU": {"legal_entity": "VMG Luxembourg S.A.", "location": "Luxembourg", "currency": "EUR", "pay_factor": 1.05, "locale": "fr_FR"},
    "UK": {"legal_entity": "VMG UK Ltd", "location": "London", "currency": "GBP", "pay_factor": 1.10, "locale": "en_GB"},
}
# Local currency units per EUR. Only used to *generate* salaries; reporting converts
# with real ECB rates (src/fetch_external.py).
GEN_FX = {"EUR": 1.0, "CZK": 25.0, "GBP": 0.85}

# Full-time base salary in EUR for a Frankfurt employee, by pay grade.
BASE_EUR = {1: 45_000, 2: 55_000, 3: 68_000, 4: 82_000, 5: 98_000, 6: 125_000, 7: 175_000}

# Share of women by grade: fewer women in senior grades is what produces a raw
# ("unadjusted") pay gap that is much larger than the like-for-like gap.
P_FEMALE = {1: 0.56, 2: 0.50, 3: 0.45, 4: 0.40, 5: 0.32, 6: 0.25, 7: 0.20}
FEMALE_PAY_FACTOR = 0.96  # ~3-4% like-for-like gap within the same grade
# Leaders are set by hand (17 heads is too few to leave to chance): 4 women at the start,
# a 5th when a woman is appointed Head of Information Security in May 2026.
FEMALE_LEADERS = {"Corporate Functions", "Clearing Operations", "People & Culture", "Client Services"}


@dataclass(frozen=True)
class Dept:
    division: str
    name: str
    cost_center: str
    start_size: int  # incl. department head, excl. division head
    entity_mix: dict  # where today's staff sit
    hire_mix: dict  # where new hires go (Prague hub grows)
    growth_per_month: float  # expected net-new roles per month
    family: str


DEPTS = [
    Dept("Executive Board", "Executive Office", "CC-0100", 0, {"DE": 1}, {"DE": 1}, 0.0, "exec"),
    Dept("Markets", "Trading Services", "CC-1100", 26, {"DE": .6, "UK": .3, "LU": .1}, {"DE": .5, "UK": .3, "CZ": .2}, 0.07, "markets"),
    Dept("Markets", "Listings & Issuer Services", "CC-1200", 16, {"DE": .5, "LU": .5}, {"DE": .5, "LU": .5}, 0.03, "markets"),
    Dept("Markets", "Market Data", "CC-1300", 14, {"DE": .4, "CZ": .4, "UK": .2}, {"CZ": .7, "DE": .3}, 0.10, "data"),
    Dept("Operations", "Clearing Operations", "CC-2100", 14, {"CZ": .6, "DE": .4}, {"CZ": .85, "DE": .15}, 0.26, "ops"),
    Dept("Operations", "Settlement Operations", "CC-2200", 12, {"CZ": .6, "LU": .4}, {"CZ": .85, "LU": .15}, 0.22, "ops"),
    Dept("Operations", "Client Services", "CC-2300", 12, {"CZ": .7, "UK": .3}, {"CZ": .9, "UK": .1}, 0.20, "ops"),
    Dept("Technology", "Platform Engineering", "CC-3100", 36, {"CZ": .5, "DE": .5}, {"CZ": .8, "DE": .2}, 0.40, "tech"),
    Dept("Technology", "IT Infrastructure", "CC-3200", 20, {"CZ": .5, "DE": .5}, {"CZ": .8, "DE": .2}, 0.16, "tech"),
    Dept("Technology", "Information Security", "CC-3300", 12, {"DE": .6, "CZ": .4}, {"DE": .5, "CZ": .5}, 0.08, "tech"),
    Dept("Corporate Functions", "Finance", "CC-4100", 16, {"DE": .6, "CZ": .4}, {"CZ": .6, "DE": .4}, 0.07, "corp"),
    Dept("Corporate Functions", "People & Culture", "CC-4200", 12, {"DE": .5, "CZ": .5}, {"CZ": .6, "DE": .4}, 0.06, "corp"),
    Dept("Corporate Functions", "Legal & Compliance", "CC-4300", 12, {"DE": .7, "LU": .3}, {"DE": .7, "LU": .3}, 0.03, "corp"),
    Dept("Corporate Functions", "Risk Management", "CC-4400", 10, {"DE": .6, "LU": .4}, {"DE": .6, "LU": .4}, 0.03, "corp"),
    # Created by the Q3 2026 reorganization (effective 2026-07-01)
    Dept("Technology", "Platform & Infrastructure", "CC-3150", 0, {"CZ": .5, "DE": .5}, {"CZ": .8, "DE": .2}, 0.56, "tech"),
    Dept("Technology", "Data & Analytics", "CC-3400", 0, {"CZ": .5, "DE": .5}, {"CZ": .7, "DE": .3}, 0.10, "data"),
]
DEPT = {d.name: d for d in DEPTS}
REORG_MAP = {  # old department -> new department
    "Market Data": "Data & Analytics",
    "Platform Engineering": "Platform & Infrastructure",
    "IT Infrastructure": "Platform & Infrastructure",
}
DIVISIONS = ["Markets", "Operations", "Technology", "Corporate Functions"]

CORP_PREFIX = {"Finance": "Finance", "People & Culture": "HR", "Legal & Compliance": "Compliance", "Risk Management": "Risk"}
FAMILY_TITLES = {
    "ops": ["Operations Associate", "Operations Analyst", "Senior Operations Analyst", "Operations Specialist"],
    "tech": ["Associate Engineer", "Engineer", "Senior Engineer", "Principal Engineer"],
    "markets": ["Markets Associate", "Markets Analyst", "Senior Markets Analyst", "Markets Specialist"],
    "data": ["Data Associate", "Data Analyst", "Senior Data Analyst", "Data Specialist"],
}

VOLUNTARY_REASONS = ["Resignation - Career Opportunity", "Resignation - Compensation",
                     "Resignation - Personal Reasons", "Resignation - Relocation"]
VOLUNTARY_P = [0.45, 0.20, 0.25, 0.10]
INVOLUNTARY_REASONS = ["Dismissal - Performance", "Redundancy"]

TERMINATION_REASONS = [  # written to data/reference/termination_reasons.csv
    ("Resignation - Career Opportunity", "Voluntary", "Yes", "Career move"),
    ("Resignation - Compensation", "Voluntary", "Yes", "Pay"),
    ("Resignation - Personal Reasons", "Voluntary", "Yes", "Personal"),
    ("Resignation - Relocation", "Voluntary", "Yes", "Relocation"),
    ("Dismissal - Performance", "Involuntary", "No", "Performance"),
    ("Redundancy", "Involuntary", "No", "Redundancy"),
    ("End of Fixed-Term Contract", "Involuntary", "No", "Contract ended"),
    ("Retirement", "Retirement", "No", "Retirement"),
]

fakers = {}
for i, (code, ent) in enumerate(ENTITIES.items()):
    fakers[code] = Faker(ent["locale"])
    fakers[code].seed_instance(SEED + i)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def month_end(d: date) -> date:
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


def add_months(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    return date(d.year + y, m + 1, 1)


def months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def pick(mix: dict) -> str:
    keys = list(mix)
    return str(rng.choice(keys, p=np.array([mix[k] for k in keys]) / sum(mix.values())))


def random_day(month: date, lo: int = 1, hi: int = 28) -> date:
    return date(month.year, month.month, int(rng.integers(lo, hi + 1)))


def sample(items: list, n: int) -> list:
    """n distinct items, chosen by index so we get the original objects back (not copies)."""
    return [items[i] for i in rng.choice(len(items), size=n, replace=False)]


def dept_exists(name: str, month: date) -> bool:
    """Departments before/after the Q3 2026 reorganization."""
    d = DEPT[name]
    if d.family == "exec":
        return False
    return name not in REORG_MAP if month >= REORG_DATE else d.start_size > 0


# ---------------------------------------------------------------------------
# The employee record (one row of "Job Information" as of today)
# ---------------------------------------------------------------------------

@dataclass
class Emp:
    pid: str
    first: str
    last: str
    gender: str
    entity: str
    dept: str
    grade: int | None  # None for externals
    role: str  # ceo / div_head / dept_head / team_lead / staff / external
    emp_class: str  # Permanent / Fixed-Term / External
    hire_date: date
    fte: float
    manager: str | None
    salary_ft: float | None  # full-time annual base salary, local currency
    title: str = ""
    event: str = "Hire"
    event_reason: str = "New Hire"
    event_date: date | None = None
    status: str = "Active"
    regret: str = ""
    term_date: date | None = None
    fixed_term_end: date | None = None
    protected: bool = False  # scripted people the random processes must not touch

    def set_event(self, event: str, reason: str, when: date) -> None:
        self.event, self.event_reason, self.event_date = event, reason, when


class Company:
    def __init__(self) -> None:
        self.people: dict[str, Emp] = {}
        self._next_id = 100001
        self.replacement_queue: list[tuple[str, date]] = []
        self.scripted: dict[str, str] = {}  # tag -> Person ID, for people later demos rely on

    # -- creation ---------------------------------------------------------
    def new_pid(self) -> str:
        pid = str(self._next_id)
        self._next_id += 1
        return pid

    def make_person(self, dept: str, grade: int | None, role: str, entity: str, hire_date: date,
                    emp_class: str = "Permanent", gender: str | None = None) -> Emp:
        if gender is None:
            gender = "Female" if grade and rng.random() < P_FEMALE[grade] else "Male"
            if grade is None:  # externals
                gender = "Female" if rng.random() < 0.35 else "Male"
        fk = fakers[entity]
        if gender == "Female":
            first = fk.first_name_female()
        elif gender == "Male":
            first = fk.first_name_male()
        else:
            first = fk.first_name()
        last = {"Female": fk.last_name_female, "Male": fk.last_name_male}.get(gender, fk.last_name)()
        fte = 1.0 if emp_class == "External" else float(rng.choice([1.0, 0.8, 0.5], p=[0.90, 0.07, 0.03]))
        salary = None
        if grade is not None:
            eur = BASE_EUR[grade] * ENTITIES[entity]["pay_factor"] * float(rng.lognormal(0, 0.07))
            if gender == "Female":
                eur *= FEMALE_PAY_FACTOR
            salary = eur * GEN_FX[ENTITIES[entity]["currency"]]
        e = Emp(self.new_pid(), first, last, gender, entity, dept, grade, role, emp_class,
                hire_date, fte, None, salary)
        e.title = self.title_for(e)
        e.set_event("Hire", "External Engagement" if emp_class == "External" else "New Hire", hire_date)
        if emp_class == "Fixed-Term":
            e.fixed_term_end = month_end(add_months(hire_date, int(rng.integers(6, 19))))
        self.people[e.pid] = e
        return e

    def title_for(self, e: Emp) -> str:
        d = DEPT[e.dept]
        if e.role == "ceo":
            return "Chief Executive Officer"
        if e.role == "external":
            return "External Consultant"
        if e.role == "div_head":
            return f"Head of {d.division}"
        if e.role == "dept_head":
            return f"Head of {e.dept}"
        if e.role == "team_lead":
            return f"Team Lead, {e.dept}"
        if d.family == "exec":
            return {2: "Executive Assistant", 5: "Chief of Staff"}.get(e.grade, "Executive Associate")
        if d.family == "corp":
            p = CORP_PREFIX[e.dept]
            return [f"{p} Associate", f"{p} Analyst", f"Senior {p} Analyst", f"{p} Expert"][e.grade - 1]
        return FAMILY_TITLES[d.family][e.grade - 1]

    # -- queries ----------------------------------------------------------
    def active(self, internal_only: bool = False) -> list[Emp]:
        return [e for e in self.people.values()
                if e.status == "Active" and (not internal_only or e.emp_class != "External")]

    def reports_of(self, pid: str) -> list[Emp]:
        return [e for e in self.active() if e.manager == pid]

    def pick_manager(self, dept: str) -> str:
        """New joiners go to the team lead (or head) in the department with the fewest reports."""
        leads = [e for e in self.active() if e.dept == dept and e.role == "team_lead"]
        if not leads:
            leads = [e for e in self.active() if e.dept == dept and e.role == "dept_head"]
        return min(leads, key=lambda m: (len(self.reports_of(m.pid)), m.pid)).pid

    def head_of(self, dept: str) -> Emp:
        return next(e for e in self.active() if e.dept == dept and e.role == "dept_head")

    def div_head(self, division: str) -> Emp:
        return next(e for e in self.active() if e.role == "div_head" and DEPT[e.dept].division == division)


# ---------------------------------------------------------------------------
# Initial population (as of 1 Sep 2024)
# ---------------------------------------------------------------------------

def initial_hire_date(role: str) -> date:
    years = float(rng.exponential(4.5)) + (3.0 if role in ("dept_head", "div_head", "ceo") else 0.0)
    years = min(max(years, 1 / 12), 17.0)
    d = date.fromordinal(FIRST_MONTH.toordinal() - int(years * 365.25))
    return d if rng.random() < 0.5 else date(d.year, d.month, 1)  # many contracts start on the 1st


def build_initial(co: Company) -> None:
    ceo = co.make_person("Executive Office", 7, "ceo", "DE", initial_hire_date("ceo"), gender="Male")
    for grade in (5, 2):
        e = co.make_person("Executive Office", grade, "staff", "DE", initial_hire_date("staff"))
        e.manager = ceo.pid
        e.protected = True

    for division in DIVISIONS:
        depts = [d for d in DEPTS if d.division == division and d.start_size > 0]
        head = co.make_person(depts[0].name, 7, "div_head", "DE", initial_hire_date("div_head"),
                              gender="Female" if division in FEMALE_LEADERS else "Male")
        head.manager = ceo.pid
        for d in depts:
            dh = co.make_person(d.name, 6, "dept_head", pick(d.entity_mix), initial_hire_date("dept_head"),
                                gender="Female" if d.name in FEMALE_LEADERS else "Male")
            dh.manager = head.pid
            n_staff = d.start_size - 1
            n_leads = n_staff // 9 if n_staff > 12 else 0
            leads = []
            for _ in range(n_leads):
                tl = co.make_person(d.name, 5, "team_lead", pick(d.entity_mix), initial_hire_date("team_lead"))
                tl.manager = dh.pid
                leads.append(tl)
            managers = leads or [dh]
            for i in range(n_staff - n_leads):
                grade = int(rng.choice([1, 2, 3, 4], p=[0.15, 0.35, 0.32, 0.18]))
                hd = initial_hire_date("staff")
                cls = "Fixed-Term" if (grade <= 3 and rng.random() < 0.07) else "Permanent"
                e = co.make_person(d.name, grade, "staff", pick(d.entity_mix), hd, emp_class=cls)
                e.manager = managers[i % len(managers)].pid
                if cls == "Fixed-Term":
                    e.fixed_term_end = month_end(add_months(FIRST_MONTH, int(rng.integers(1, 15))))

    # External contractors: excluded from headcount, but they show up in the exports.
    for dept, entity, n in [("Platform Engineering", "CZ", 3), ("IT Infrastructure", "CZ", 2),
                            ("Information Security", "DE", 1), ("Settlement Operations", "CZ", 1),
                            ("Trading Services", "DE", 1)]:
        for _ in range(n):
            x = co.make_person(dept, None, "external", entity,
                               date.fromordinal(FIRST_MONTH.toordinal() - int(rng.integers(30, 500))),
                               emp_class="External")
            x.manager = co.pick_manager(dept)

    # Two people who did not declare a gender (shows the n<5 suppression rule in action).
    staff = [e for e in co.active(True) if e.role == "staff"]
    for e in sample(staff, 2):
        e.gender = "Undeclared"

    # The most recent event for people hired before the last salary review is the review itself.
    for e in co.people.values():
        if e.emp_class != "External" and e.hire_date < date(2024, 4, 1):
            e.set_event("Pay Rate Change", "Annual Salary Review", date(2024, 4, 1))


# ---------------------------------------------------------------------------
# Monthly simulation
# ---------------------------------------------------------------------------

def hire(co: Company, dept: str, month: date, day: date | None = None, grade: int | None = None,
         entity: str | None = None, **kw) -> Emp:
    d = DEPT[dept]
    grade = grade or int(rng.choice([1, 2, 3, 4], p=[0.30, 0.40, 0.22, 0.08]))
    entity = entity or pick(d.hire_mix)
    day = day or (date(month.year, month.month, 1) if rng.random() < 0.6 else random_day(month, 2, 28))
    cls = kw.pop("emp_class", "Fixed-Term" if (grade <= 3 and rng.random() < 0.10) else "Permanent")
    e = co.make_person(dept, grade, "staff", entity, day, emp_class=cls, **kw)
    e.manager = co.pick_manager(dept)
    return e


def terminate(co: Company, e: Emp, when: date, reason: str, regret: str = "No") -> None:
    e.status = "Terminated"
    e.term_date = when
    e.regret = regret
    e.set_event("Termination", reason, when)


def simulate_month(co: Company, month: date) -> list[Emp]:
    """Apply one month of events; return everyone who must appear in this month's export."""
    end = month_end(month)
    leavers: list[Emp] = []

    # Annual salary review every 1 April: +3% on average for everyone already employed.
    if month.month == 4:
        for e in co.active(True):
            if e.hire_date < month:
                e.salary_ft *= float(rng.normal(1.03, 0.01))
                e.set_event("Pay Rate Change", "Annual Salary Review", month)

    # Leadership change: Head of Information Security retires, a new head is hired.
    if month == LEADERSHIP_CHANGE_MONTH:
        old = co.head_of("Information Security")
        new = co.make_person("Information Security", 6, "dept_head", "DE", date(2026, 5, 4), gender="Female")
        new.manager = old.manager
        new.protected = True
        for r in co.reports_of(old.pid):
            r.manager = new.pid
            r.set_event("Data Change", "Manager Change", date(2026, 5, 4))
        terminate(co, old, end, "Retirement")
        leavers.append(old)

    # Q3 2026 reorganization (1 Jul 2026).
    if month == REORG_DATE:
        tech_head = co.div_head("Technology")
        pe_head, it_head, md_head = (co.head_of(n) for n in ("Platform Engineering", "IT Infrastructure", "Market Data"))
        for e in co.active():
            if e.dept in REORG_MAP:
                e.dept = REORG_MAP[e.dept]
                if e.emp_class != "External":
                    e.set_event("Reorganization", "Q3 2026 Reorganization", REORG_DATE)
        it_head.manager = pe_head.pid  # becomes deputy head of the merged department
        it_head.role = "team_lead"
        md_head.manager = tech_head.pid
        for e in co.active():
            e.title = co.title_for(e)
        it_head.title = "Deputy Head, Platform & Infrastructure"

    # Fixed-term contracts ending this month: ~60% are made permanent.
    for e in co.active(True):
        if e.fixed_term_end and month <= e.fixed_term_end <= end and not e.protected:
            if rng.random() < 0.6:
                e.set_event("Data Change", "Contract Conversion to Permanent", e.fixed_term_end)
                e.emp_class, e.fixed_term_end = "Permanent", None
            else:
                terminate(co, e, e.fixed_term_end, "End of Fixed-Term Contract")
                leavers.append(e)

    # Resignations, dismissals, retirements (managers are kept stable on purpose).
    for e in co.active(True):
        if e.role not in ("staff", "team_lead") or e.protected or e.hire_date >= month:
            continue
        division = DEPT[e.dept].division
        tenure = months_between(e.hire_date, month)
        vol = 0.07 * (1.5 if division == "Technology" else 1.0) * (0.6 if e.role == "team_lead" else 1.0)
        invol = 0.02
        if tenure < 12:
            vol *= 5.0 if division == "Operations" else 2.0  # Operations struggles to keep new joiners
            invol *= 1.5
        p_vol, p_invol = 1 - (1 - vol) ** (1 / 12), 1 - (1 - invol) ** (1 / 12)
        u = rng.random()
        if u < p_vol:
            when = end if rng.random() < 0.5 else random_day(month, 5, 28)
            reason = str(rng.choice(VOLUNTARY_REASONS, p=VOLUNTARY_P))
            regret = "Yes" if rng.random() < (0.6 if (e.grade or 0) >= 3 else 0.35) else "No"
            terminate(co, e, when, reason, regret)
        elif u < p_vol + p_invol:
            terminate(co, e, random_day(month, 5, 28), str(rng.choice(INVOLUNTARY_REASONS, p=[0.7, 0.3])))
        elif tenure > 240 and rng.random() < 0.01:
            terminate(co, e, end, "Retirement")
        else:
            continue
        leavers.append(e)
        if e.role == "team_lead":  # their team moves to the department head on the leaving date
            for r in co.reports_of(e.pid):
                r.manager = co.head_of(e.dept).pid
                r.set_event("Data Change", "Manager Change", e.term_date)
        if rng.random() < 0.75:  # most leavers are replaced 1-2 months later
            co.replacement_queue.append((e.dept, add_months(month, int(rng.integers(1, 3)))))

    # Promotions and lateral transfers (effective on the 1st).
    for e in co.active(True):
        if e.role != "staff" or e.protected or e.status != "Active" or e.hire_date >= month:
            continue
        if e.grade <= 3 and months_between(e.hire_date, month) >= 12 and rng.random() < 0.006:
            e.grade += 1
            e.salary_ft *= 1.08
            e.title = co.title_for(e)
            e.set_event("Promotion", "Promotion", month)
        elif rng.random() < 0.0025:
            valid = [d.name for d in DEPTS if dept_exists(d.name, month) and d.name != e.dept]
            same_division = [n for n in valid if DEPT[n].division == DEPT[e.dept].division]
            options = same_division if (same_division and rng.random() < 0.7) else valid
            if options:
                e.dept = str(rng.choice(options))
                e.manager = co.pick_manager(e.dept)
                e.title = co.title_for(e)
                e.set_event("Transfer", "Lateral Transfer", month)

    # Hiring: growth roles plus replacements that fall due this month.
    active_depts = [d for d in DEPTS if dept_exists(d.name, month)]
    for d in active_depts:
        for _ in range(int(rng.poisson(d.growth_per_month))):
            hire(co, d.name, month)
    due = [(dept, m) for dept, m in co.replacement_queue if m == month]
    co.replacement_queue = [(dept, m) for dept, m in co.replacement_queue if m != month]
    for dept, _ in due:
        hire(co, REORG_MAP.get(dept, dept) if month >= REORG_DATE else dept, month)

    # Scripted events that later demos rely on.
    if month == date(2026, 3, 1):  # pre-entered in the Feb export -> future-dated record
        e = hire(co, "Platform Engineering", month, day=date(2026, 3, 2), grade=2, entity="CZ", emp_class="Permanent")
        e.protected = True
        co.scripted["feb_future_hire"] = e.pid
    if month == DROPIN_MONTH:  # Ticket #4711: both are pre-entered in the Sep export
        p = co.people[co.scripted["ticket_transfer"]]
        p.dept = "Client Services"
        p.manager = co.pick_manager("Client Services")
        p.title = co.title_for(p)
        p.set_event("Transfer", "Lateral Transfer", DROPIN_MONTH)
        f = hire(co, "Settlement Operations", month, day=date(2026, 10, 15), grade=2, entity="CZ",
                 emp_class="Permanent", gender="Female")
        f.protected = True
        co.scripted["ticket_future_hire"] = f.pid

    return [e for e in co.people.values()
            if e.status == "Active" and e.hire_date <= end] + leavers


# ---------------------------------------------------------------------------
# Export rows
# ---------------------------------------------------------------------------

def to_row(e: Emp) -> dict:
    d = DEPT[e.dept]
    ent = ENTITIES[e.entity]
    salary = ""
    if e.salary_ft is not None:
        actual = e.salary_ft * e.fte
        salary = int(round(actual, -3)) if ent["currency"] == "CZK" else int(round(actual, -2))
    return {
        "Person ID External": e.pid, "First Name": e.first, "Last Name": e.last, "Gender": e.gender,
        "Employee Status": e.status, "Employee Class": e.emp_class, "Hire Date": e.hire_date,
        "Event": e.event, "Event Reason": e.event_reason, "Event Date": e.event_date,
        "Regret Termination": e.regret if e.status == "Terminated" else "",
        "Division": d.division, "Department": e.dept, "Cost Center": d.cost_center,
        "Legal Entity": ent["legal_entity"], "Location": ent["location"], "Job Title": e.title,
        "Pay Grade": f"G{e.grade}" if e.grade else "", "FTE": f"{e.fte:.1f}",
        "Manager ID": e.manager or "", "Annual Salary": salary,
        "Currency": ent["currency"] if e.emp_class != "External" else "",
    }


def write_csv(path: Path, rows: list[dict], date_fmt: str = "%Y-%m-%d") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            out = dict(r)
            for col in ("Hire Date", "Event Date"):
                if isinstance(out[col], date):
                    out[col] = out[col].strftime(date_fmt)
            w.writerow(out)


# ---------------------------------------------------------------------------
# Planted data-quality issues (the answer key)
# ---------------------------------------------------------------------------

def plant_issues(exports: dict[str, list[dict]], co: Company) -> list[dict]:
    key: list[dict] = []

    def log(file: str, pid: str, rule: str, name: str, detail: str) -> None:
        key.append({"File": f"{file}.csv", "Person ID External": pid, "Rule ID": rule, "Rule": name, "Detail": detail})

    def internal_active(file: str, **filters) -> list[dict]:
        return [r for r in exports[file] if r["Employee Status"] == "Active" and r["Employee Class"] != "External"
                and r["Job Title"] != "Chief Executive Officer" and all(r[k] == v for k, v in filters.items())]

    # DQ05 - inconsistent location labels (fixed by standardising, still counted)
    for r in sample(internal_active("2025-10", Location="Prague"), 4):
        r["Location"] = "Praha"
        log("2025-10", r["Person ID External"], "DQ05", "Location label not standard", "Praha instead of Prague")
    for r in sample(internal_active("2026-06", Location="Prague"), 3):
        r["Location"] = " Prague "
        log("2026-06", r["Person ID External"], "DQ05", "Location label not standard", "leading/trailing spaces")

    # DQ06 - whole file exported with German date format (dd.MM.yyyy)
    log("2025-11", "", "DQ06", "Non-ISO date format", "all dates in file are dd.MM.yyyy")

    # DQ01 - exact duplicate rows
    for file, n in (("2025-11", 2), ("2026-05", 1)):
        for r in sample(internal_active(file), n):
            exports[file].append(dict(r))
            log(file, r["Person ID External"], "DQ01", "Duplicate row", "exact duplicate of another row")

    # DQ02 - missing manager
    for r in sample(internal_active("2026-01"), 2):
        r["Manager ID"] = ""
        log("2026-01", r["Person ID External"], "DQ02", "Missing manager", "Manager ID is blank")

    # DQ03 - manager ID not found in the same export (stale: points at someone who already left)
    earlier = [f for f in sorted(exports) if f < "2026-03"]
    stale_file, stale_pid = next((f, r["Person ID External"]) for f in reversed(earlier)
                                 for r in exports[f] if r["Employee Status"] == "Terminated")
    r = sample(internal_active("2026-03"), 1)[0]
    r["Manager ID"] = stale_pid
    log("2026-03", r["Person ID External"], "DQ03", "Manager not found", f"Manager ID {stale_pid} left in {stale_file}")

    # DQ04 - future-dated records (entered in the HRIS before they take effect)
    fh = next(r for r in exports["2026-03"] if r["Person ID External"] == co.scripted["feb_future_hire"])
    exports["2026-02"].append(dict(fh))
    log("2026-02", fh["Person ID External"], "DQ04", "Future-dated record", "hire effective 2026-03-02")
    for tag, detail in (("ticket_transfer", "transfer to Client Services effective 2026-10-01"),
                        ("ticket_future_hire", "hire effective 2026-10-15")):
        row = next(r for r in exports["2026-10"] if r["Person ID External"] == co.scripted[tag])
        exports["2026-09"].append(dict(row))
        log("2026-09", row["Person ID External"], "DQ04", "Future-dated record", detail)

    # DQ07 - salary currency does not match the legal entity
    r = sample(internal_active("2026-04", Location="Prague"), 1)[0]
    r["Currency"] = "EUR"
    log("2026-04", r["Person ID External"], "DQ07", "Currency mismatch", "EUR on a Czech contract (amount is CZK)")

    # DQ08 - FTE out of range (left for Kamal to catch: the D1 "your turn" exercise)
    r = sample(internal_active("2026-07"), 1)[0]
    r["FTE"] = "10.0"
    log("2026-07", r["Person ID External"], "DQ08", "FTE outside 0-1", "FTE typed as 10.0 instead of 1.0")

    # Shuffle row order so duplicates and future rows are not all at the bottom.
    for file in exports:
        exports[file] = sample(exports[file], len(exports[file]))
    return key


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    co = Company()
    build_initial(co)

    # Ticket #4711: a Markets employee who will be transferred to Operations on 1 Oct 2026.
    candidate = next(e for e in co.active(True) if e.dept == "Trading Services" and e.role == "staff" and e.grade == 3)
    candidate.protected = True
    co.scripted["ticket_transfer"] = candidate.pid

    exports: dict[str, list[dict]] = {}
    month = FIRST_MONTH
    while month <= DROPIN_MONTH:
        exports[month.strftime("%Y-%m")] = [to_row(e) for e in simulate_month(co, month)]
        month = add_months(month, 1)

    key = plant_issues(exports, co)

    for file, rows in exports.items():
        folder = DATA / ("demo_dropin" if file == DROPIN_MONTH.strftime("%Y-%m") else "exports")
        write_csv(folder / f"{file}.csv", rows, date_fmt="%d.%m.%Y" if file == "2025-11" else "%Y-%m-%d")

    ref = DATA / "reference"
    ref.mkdir(parents=True, exist_ok=True)
    with (ref / "planted_issues.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["File", "Person ID External", "Rule ID", "Rule", "Detail"])
        w.writeheader()
        w.writerows(key)
    with (ref / "termination_reasons.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Event Reason", "Leaver Category", "Is Voluntary", "Reason Short"])
        w.writerows(TERMINATION_REASONS)

    with (ref / "legal_entities.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Legal Entity", "Entity Code", "Country", "Location", "Currency"])
        country = {"DE": "Germany", "CZ": "Czechia", "LU": "Luxembourg", "UK": "United Kingdom"}
        for code, ent in ENTITIES.items():
            w.writerow([ent["legal_entity"], code, country[code], ent["location"], ent["currency"]])

    write_ticket_list(exports, co)

    # Console summary
    print(f"{'month':8} {'rows':>5} {'internal HC':>12}")
    for file, rows in exports.items():
        hc = len({r["Person ID External"] for r in rows if r["Employee Status"] == "Active"
                  and r["Employee Class"] != "External" and str(r["Event Date"]) <= month_end(date.fromisoformat(file + "-01")).isoformat()})
        print(f"{file:8} {len(rows):5} {hc:12}")
    print(f"\nPlanted issues: {len(key)}  ->  data/reference/planted_issues.csv")


def write_ticket_list(exports: dict[str, list[dict]], co: Company) -> None:
    """The HRBP's own Operations list, pulled from the HRIS on 2 Oct 2026 'as of today,
    including future-dated records and all employee classes'."""
    sep = exports["2026-09"]
    rows = [r for r in sep if r["Division"] == "Operations" and r["Employee Status"] == "Active"]
    seen, out = set(), []
    for r in sorted(rows, key=lambda r: (r["Last Name"], r["First Name"])):
        if r["Person ID External"] in seen:
            continue
        seen.add(r["Person ID External"])
        out.append({k: r[k] for k in ("Person ID External", "First Name", "Last Name", "Department",
                                       "Employee Class", "Event", "Event Date")})
    path = DATA / "ticket" / "hrbp_operations_list_2026-10-02.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        for r in out:
            r = dict(r)
            if isinstance(r["Event Date"], date):
                r["Event Date"] = r["Event Date"].isoformat()
            w.writerow(r)


if __name__ == "__main__":
    main()
