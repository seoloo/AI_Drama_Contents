"""유료 API 호출 전 예상 비용 계산과 확인."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Callable


class CostDeclined(RuntimeError):
    """사용자가 비용을 승인하지 않았거나 상한을 넘었을 때."""


@dataclass
class CostLine:
    provider: str
    item: str
    quantity: float
    unit: str
    unit_price: float
    verified: bool = True  # 공식 가격표로 확인한 단가인지
    price_label: str = ""  # 표에 보여 줄 단가 (예: "$4.00/1M tok")

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class CostEstimate:
    step: str
    lines: list[CostLine] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(line.subtotal for line in self.lines)

    def render(self) -> str:
        out = [f"[예상 비용] {self.step}"]
        out.append(f"  {'항목':<28}{'수량':>12}  {'단가':>12}  {'소계':>9}")
        for ln in self.lines:
            mark = "" if ln.verified else " *"
            qty = f"{ln.quantity:,.0f} {ln.unit}"
            price = ln.price_label or f"${ln.unit_price:.4f}/{ln.unit}"
            out.append(
                f"  {ln.provider + ' / ' + ln.item:<28}{qty:>12}  {price:>14}  ${ln.subtotal:>8.4f}{mark}"
            )
        out.append(f"  {'합계':<28}{'':>12}  {'':>12}  ${self.total:>8.4f}")
        if any(not ln.verified for ln in self.lines):
            out.append("  * 공식 가격표로 아직 확인하지 않은 단가입니다 (config/settings.yaml 의 pricing)")
        out.extend(f"  - {n}" for n in self.notes)
        return "\n".join(out)


ConfirmFn = Callable[[CostEstimate], bool]


def interactive_confirm(estimate: CostEstimate) -> bool:
    print(estimate.render())
    if not sys.stdin or not sys.stdin.isatty():
        print("대화형 터미널이 아니어서 확인을 받을 수 없습니다. 중단합니다.")
        return False
    answer = input("이 비용으로 진행할까요? [y/N] ").strip().lower()
    return answer in ("y", "yes", "ㅛ")


def require_approval(estimate: CostEstimate, confirm: ConfirmFn, max_cost: float) -> None:
    """비용이 0 이면 통과, 상한 초과면 중단, 그 외에는 사용자 확인."""
    if estimate.total <= 0:
        return
    if estimate.total > max_cost:
        print(estimate.render())
        raise CostDeclined(
            f"예상 비용 ${estimate.total:.2f} 가 1회 상한 ${max_cost:.2f} 를 넘습니다 "
            "(settings.yaml 의 max_cost_per_run_usd)"
        )
    if not confirm(estimate):
        raise CostDeclined("비용 승인을 받지 못해 중단했습니다")


def claude_price(settings, model: str) -> tuple[float, float, bool]:
    table = settings.get("pricing.claude", {}) or {}
    entry = table.get(model)
    if not entry:
        raise CostDeclined(f"pricing.claude 에 {model} 단가가 없습니다. 단가를 먼저 넣어 주세요")
    return float(entry["input_per_mtok"]), float(entry["output_per_mtok"]), bool(table.get("verified"))
