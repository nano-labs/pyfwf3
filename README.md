### TODOS:
- Recursive special filters like: birthday__year__lt
- Filter with same line like: .filter(start_day=end_day)
- Multi-column order like: .order_by("name", "age")
- Values using special fields like: .values("name__len")
- Order using special fields like: .order_by("birthday__year")
- repr() show attributes created on _before_parse()