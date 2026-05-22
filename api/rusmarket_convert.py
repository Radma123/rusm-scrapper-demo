from models.result import ReturnResult, parse_price_rub


def _price_from_block(block: dict) -> int:
    for key in ("price", "price_rub", "min_price", "cost"):
        val = block.get(key)
        if val is not None:
            try:
                return parse_price_rub(val)
            except (ValueError, TypeError):
                continue
    return 0


def _link_from_block(block: dict, serial: str) -> str:
    for key in ("url", "link", "product_url"):
        val = block.get(key)
        if val:
            return str(val)
    return f"https://rusmarket.top/?q={serial}"


def _desc_from_block(block: dict) -> str | None:
    parts: list[str] = []
    for key in ("available", "count", "quantity", "stock"):
        if key in block and block[key] is not None:
            parts.append(f"{key}: {block[key]}")
    if not parts and block:
        parts.append(str(block)[:300])
    return "; ".join(parts) if parts else None


def availability_to_results(items: list[dict]) -> list[ReturnResult]:
    """Преобразует ответ Rusmarket API в список ReturnResult."""
    out: list[ReturnResult] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        serial = str(item.get("serial") or "").strip()
        name = (item.get("name") or serial or "Товар").strip()

        local = item.get("local")
        if isinstance(local, dict) and local:
            out.append(
                ReturnResult(
                    title=name,
                    link=_link_from_block(local, serial),
                    price=_price_from_block(local),
                    description=_desc_from_block(local) or f"Артикул: {serial}",
                    photo_url=local.get("photo_url") or local.get("image"),
                    source="rusmarket",
                )
            )

        external = item.get("external")
        if isinstance(external, dict):
            for ext_name, ext_data in external.items():
                if not isinstance(ext_data, dict) or not ext_data:
                    continue
                out.append(
                    ReturnResult(
                        title=f"{name} — {ext_name}",
                        link=_link_from_block(ext_data, serial),
                        price=_price_from_block(ext_data),
                        description=_desc_from_block(ext_data),
                        photo_url=ext_data.get("photo_url") or ext_data.get("image"),
                        source="rusmarket",
                    )
                )

        if not local and (not external or not isinstance(external, dict)):
            out.append(
                ReturnResult(
                    title=name,
                    link=f"https://rusmarket.top/?q={serial}",
                    price=0,
                    description=f"Артикул: {serial}" if serial else None,
                    photo_url=None,
                    source="rusmarket",
                )
            )
    return out
