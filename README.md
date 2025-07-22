# 🔁 HA YAML Converter

A powerful converter for Home Assistant automations: automatically transforms YAML syntax from the legacy format (`HA ≤ 2024.9`) to the new format (`HA ≥ 2024.10`). Perfect for those with dozens of automations who don’t want to migrate manually 🤯.

## 🧠 Key Features

- ✅ Automatic renaming of keys: `trigger → triggers`, `condition → conditions`, `action → actions`
- 📁 Supports single files and entire directories
- 💬 Direct YAML string conversion (`--string`)
- 🧾 Preserves comments and formatting via `ruamel.yaml`
- 🧪 Dry-run mode for previewing changes without saving
- 📊 Detailed change reports and cumulative stats

## 📦 Requirements

- Python 3.6+
- Optional: `ruamel.yaml` to preserve comments

```bash
pip install ruamel.yaml
```

## 🚀 Usage

### 🔄 Convert a single file

```bash
python ha_converter.py automation.yaml
```

### 📝 Specify output file

```bash
python ha_converter.py automation.yaml -o new.yaml
```

### 👀 Preview changes (dry-run)

```bash
python ha_converter.py automation.yaml --dry-run
```

### 📂 Convert all YAML files in a directory

```bash
python ha_converter.py automations/ -d
```

### 🧵 Convert a YAML string

```bash
python ha_converter.py --string "alias: test\naction: ..."
```

### ⚙️ Extra options

| Flag            | Description                                      |
|-----------------|--------------------------------------------------|
| `--no-comments` | Disables comment and formatting preservation     |
| `--pattern`     | Specifies file pattern (`*.yaml`)                |
| `--version`     | Displays script version                          |

## 📋 Sample Report

```
✅ Kitchen Light: trigger → triggers, action → actions
⚪ Morning Alarm: already using new syntax
📊 Total automations processed: 2
```

## 👤 Credits

- 🎯 **Concept:** Pietro Molinaro  
- 🤖 **Author:** Claude, carefully adapted

## 🪪 License

Released under the **MIT License**. Use it, modify it, share it freely 🚀

