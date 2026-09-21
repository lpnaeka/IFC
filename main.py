# Лабораторная работа: работа с IFC-моделью
# Липина Екатерина Игоревна, группа 3140801/52501

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element


# --- Настройки ---
IFC_FILE = "Example_1.ifc"          # исходная модель
MODIFIED_FILE = "modified.ifc"       # сюда сохраним изменённую модель
FILTERED_FILE = "doors_filtered.ifc" # сюда сохраним подмодель с дверями
MIN_DOOR_WIDTH = 0.8                 # порог «узкой» двери


# --- Открываем модель ---
print("Открываю модель:", IFC_FILE)
model = ifcopenshell.open(IFC_FILE)
print("Схема IFC:", model.schema)
print()

# Задание 1. Подсчет количества стен в модели
print("=== Задание 1. Стены ===")
wall_list = model.by_type("IfcWall")
print(f"Количество стен в модели: {len(wall_list)}")
print()


# Задание 2. Вывод информации о первой стене
print("=== Задание 2. Первая стена ===")
if wall_list:
    wall_0 = wall_list[0]
    print(f"GlobalId:   {wall_0.GlobalId}")
    print(f"Name:       {wall_0.Name}")
    print(f"ObjectType: {getattr(wall_0, 'ObjectType', None)}")
else:
    wall_0 = None
    print("Стены не найдены.")
print()

# Задание 3. Чтение наборов свойств стены
print("=== Задание 3. Property Sets первой стены ===")
if wall_0 is not None:
    psets = ifcopenshell.util.element.get_psets(wall_0)
    print("Полный словарь psets:")
    print(psets)
    print()
    if psets:
        for pset_name, pset_props in psets.items():
            print(f"Pset: {pset_name}")
            for prop_name, prop_value in pset_props.items():
                print(f"  {prop_name}: {prop_value}")
    else:
        print("У стены нет наборов свойств.")
else:
    print("Первой стены нет.")
print()

# Задание 4. Получение этажей и информации о модели
print("=== Задание 4. Этажи ===")
storey_list = model.by_type("IfcBuildingStorey")
print(f"Количество этажей: {len(storey_list)}")
for st in storey_list:
    elevation = getattr(st, "Elevation", None)
    print(f"Этаж: {st.Name}, Elevation={elevation}")
print("TITLE: Информация о модели IFC")
print()

# Задание 5. Анализ размеров дверей и поиск "узких" дверей
print("=== Задание 5. Двери ===")
door_list = model.by_type("IfcDoor")
print(f"Всего дверей: {len(door_list)}")
for dr in door_list:
    w = getattr(dr, "OverallWidth", None)
    h = getattr(dr, "OverallHeight", None)
    print(f"Дверь: {dr.Name}, ширина={w}, высота={h}")
print()

print("=== Задание 5.1. Узкие двери ===")
narrow_list = []
for dr in door_list:
    w = getattr(dr, "OverallWidth", None)
    if w is not None and w < MIN_DOOR_WIDTH:
        narrow_list.append(dr)

if narrow_list:
    for dr in narrow_list:
        w = getattr(dr, "OverallWidth", None)
        h = getattr(dr, "OverallHeight", None)
        print(f"{dr.Name}: ширина = {round(w, 3) if w else None}, высота = {round(h, 3) if h else None}")
    print(f"Всего узких дверей: {len(narrow_list)}")
else:
    print("Узких дверей не обнаружено.")
print()

# Задание 6. Изменение свойств стены и сохранение новой модели
print("=== Задание 6. Изменение и сохранение ===")
if wall_0 is not None:
    old = wall_0.Name
    new = "MODIFIED_" + (old if old else "Wall")
    wall_0.Name = new
    print(f"Имя стены изменено: '{old}' -> '{new}'")

    target_pset = None
    for rel in getattr(wall_0, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            cand = getattr(rel, "RelatingPropertyDefinition", None)
            if cand is not None and cand.is_a("IfcPropertySet") and cand.Name == "Pset_WallCommon":
                target_pset = cand
                break

    if target_pset is None:
        target_pset = ifcopenshell.api.run(
            "pset.add_pset", model, product=wall_0, name="Pset_WallCommon"
        )

    ifcopenshell.api.run(
        "pset.edit_pset",
        model,
        pset=target_pset,
        properties={"IsExternal": True},
    )
    print("Добавлено/обновлено свойство IsExternal = True")
model.write(MODIFIED_FILE)
print(f"Модель сохранена в {MODIFIED_FILE}")

check = ifcopenshell.open(MODIFIED_FILE)
check_walls = check.by_type("IfcWall")
if check_walls:
    cw = check_walls[0]
    print(f"Проверка: имя первой стены в новом файле: {cw.Name}")
    cw_psets = ifcopenshell.util.element.get_psets(cw)
    if "Pset_WallCommon" in cw_psets:
        print(f"Проверка: Pset_WallCommon.IsExternal = {cw_psets['Pset_WallCommon'].get('IsExternal')}")
print()

# Задание 7. Фильтрация элементов по условию и экспорт подмодели
print("=== Задание 7. Подмодель дверей ===")
wide_doors = []
for dr in door_list:
    w = getattr(dr, "OverallWidth", None)
    if w is not None and w >= MIN_DOOR_WIDTH:
        wide_doors.append(dr)

print(f"Дверей, подходящих под критерий (ширина >= {MIN_DOOR_WIDTH}): {len(wide_doors)}")

# Создаём новую модель и копируем нужные элементы
submodel = ifcopenshell.file(schema=model.schema)
for t in ["IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey"]:
    for obj in model.by_type(t):
        submodel.add(obj)
for dr in wide_doors:
    submodel.add(dr)

submodel.write(FILTERED_FILE)
print(f"Подмодель сохранена в {FILTERED_FILE}")

check_sub = ifcopenshell.open(FILTERED_FILE)
print(f"Проверка: дверей в подмодели: {len(check_sub.by_type('IfcDoor'))}")
print()


print("=== Готово! ===")