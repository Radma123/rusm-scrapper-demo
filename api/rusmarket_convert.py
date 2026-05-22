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
    """Преобразует ответ Rusmarket API в список ReturnResult с учетом аналогов."""
    out: list[ReturnResult] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        serial = str(item.get("serial") or "").strip()
        name = (item.get("name") or serial or "Товар").strip()

        # 1. Обработка локальных остатков
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

        # 2. Обработка внешних поставщиков и их аналогов
        external = item.get("external")
        if isinstance(external, dict):
            for ext_name, ext_data in external.items():
                if not isinstance(ext_data, dict) or not ext_data:
                    continue
                
                # Добавляем сам оригинальный товар от внешнего поставщика
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

                # --- НОВЫЙ БЛОК: Обработка аналогов ---
                analogs = ext_data.get("analogs")
                if isinstance(analogs, list):
                    for analog in analogs:
                        if not isinstance(analog, dict):
                            continue
                        
                        # Берем артикул аналога, если его нет — используем оригинальный
                        analog_serial = str(analog.get("part_number") or serial).strip()
                        # Берем имя аналога. Если имени нет, пишем "Аналог <артикул>"
                        analog_name = (analog.get("name") or f"Аналог {analog_serial}").strip()
                        
                        # Формируем красивое описание, например с указанием статуса замены
                        desc_parts = []
                        base_desc = _desc_from_block(analog)
                        if base_desc:
                            desc_parts.append(base_desc)
                        if analog.get("replacement_status"):
                            desc_parts.append(str(analog["replacement_status"]))
                        
                        description = "; ".join(desc_parts) or f"Аналог для артикула: {serial}"

                        out.append(
                            ReturnResult(
                                title=f"[Аналог] {analog_name} — {ext_name}",
                                link=_link_from_block(analog, analog_serial),
                                price=_price_from_block(analog),
                                description=description,
                                photo_url=analog.get("photo_url") or analog.get("image"),
                                source="rusmarket",
                            )
                        )
                # --------------------------------------

        # 3. Если ничего не нашли
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