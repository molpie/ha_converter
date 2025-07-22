#!/usr/bin/env python3
"""
Convertitore YAML per automazioni di Home Assistant
Da vecchia sintassi (HA ≤ 2024.9) a nuova sintassi (HA ≥ 2024.10)

Ideatore: Pietro Molinaro
Autore: Claude
Versione: 1.0
"""

import yaml
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Union
import re
from copy import deepcopy

class HAYamlConverter:
    """Convertitore per automazioni Home Assistant da vecchia a nuova sintassi"""
    
    def __init__(self, preserve_comments=True):
        self.preserve_comments = preserve_comments
        self.changes_log = []
        self.total_stats = {'converted': 0, 'already_new': 0, 'total': 0}
        
        # Configurazione YAML per preservare ordine e formattazione
        if preserve_comments:
            from ruamel.yaml import YAML
            self.yaml_loader = YAML()
            self.yaml_loader.preserve_quotes = True
            self.yaml_loader.width = 4096
        else:
            self.yaml_loader = yaml
    
    def convert_automation(self, automation: Dict[str, Any]) -> Dict[str, Any]:
        """Converte una singola automazione dalla vecchia alla nuova sintassi"""
        converted = deepcopy(automation)
        changes = []
        alias = converted.get('alias', 'Unnamed automation')
        
        # Verifica se l'automazione è già in nuova sintassi
        if self._is_new_syntax(automation):
            self.changes_log.append(f"⚪ {alias}: già in nuova sintassi")
            return converted
        
        # Conversione trigger -> triggers
        if 'trigger' in converted:
            converted['triggers'] = self._convert_triggers(converted['trigger'])
            del converted['trigger']
            changes.append("trigger → triggers")
        
        # Conversione condition -> conditions
        if 'condition' in converted:
            converted['conditions'] = converted['condition']
            del converted['condition']
            changes.append("condition → conditions")
        
        # Conversione action -> actions
        if 'action' in converted:
            converted['actions'] = converted['action']
            del converted['action']
            changes.append("action → actions")
        
        if changes:
            self.changes_log.append(f"✓ {alias}: {', '.join(changes)}")
        
        return converted
    
    def _convert_triggers(self, triggers: Union[Dict, List[Dict]]) -> List[Dict]:
        """Converte i trigger dalla vecchia sintassi"""
        if isinstance(triggers, dict):
            triggers = [triggers]
        
        converted_triggers = []
        for trigger in triggers:
            converted_trigger = deepcopy(trigger)
            
            # Conversione platform -> trigger
            if 'platform' in converted_trigger:
                converted_trigger['trigger'] = converted_trigger['platform']
                del converted_trigger['platform']
            
            converted_triggers.append(converted_trigger)
        
        return converted_triggers
    
    def convert_file(self, input_file: Path, output_file: Path = None) -> bool:
        """Converte un file YAML completo"""
        try:
            # Lettura file
            with open(input_file, 'r', encoding='utf-8') as f:
                if self.preserve_comments:
                    data = self.yaml_loader.load(f)
                else:
                    data = yaml.safe_load(f)
            
            # Reset log modifiche per questo file
            self.changes_log = []
            
            # Conversione
            converted_data = self._convert_yaml_data(data)
            
            # Aggiorna statistiche totali
            file_stats = self.get_summary_stats()
            self.total_stats['converted'] += file_stats['converted']
            self.total_stats['already_new'] += file_stats['already_new']
            self.total_stats['total'] += file_stats['total']
            
            # Scrittura file output
            output_path = output_file or input_file.with_suffix('.new.yaml')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if self.preserve_comments:
                    self.yaml_loader.dump(converted_data, f)
                else:
                    yaml.dump(converted_data, f, default_flow_style=False, 
                             allow_unicode=True, sort_keys=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Errore durante la conversione: {e}")
            return False
    
    def _convert_yaml_data(self, data: Any) -> Any:
        """Converte i dati YAML in base alla struttura"""
        if isinstance(data, list):
            # Lista di automazioni
            return [self.convert_automation(item) if self._is_automation(item) else item 
                   for item in data]
        elif isinstance(data, dict):
            if self._is_automation(data):
                # Singola automazione
                return self.convert_automation(data)
            else:
                # Struttura più complessa (es. configuration.yaml)
                converted = {}
                for key, value in data.items():
                    if key == 'automation':
                        converted[key] = self._convert_yaml_data(value)
                    else:
                        converted[key] = value
                return converted
        
        return data
    
    def _is_automation(self, item: Dict) -> bool:
        """Verifica se un dizionario è un'automazione HA"""
        automation_keys = {'trigger', 'triggers', 'condition', 'conditions', 
                          'action', 'actions', 'alias'}
        return isinstance(item, dict) and any(key in item for key in automation_keys)
    
    def _is_new_syntax(self, automation: Dict) -> bool:
        """Verifica se un'automazione è già in nuova sintassi"""
        if not isinstance(automation, dict):
            return False
        
        # Se ha solo chiavi nuove, è già convertita
        has_new_keys = any(key in automation for key in ['triggers', 'conditions', 'actions'])
        has_old_keys = any(key in automation for key in ['trigger', 'condition', 'action'])
        
        return has_new_keys and not has_old_keys
    
    def convert_directory(self, input_dir: Path, pattern: str = "*.yaml") -> Dict[str, bool]:
        """Converte tutti i file YAML in una directory"""
        if not input_dir.is_dir():
            raise ValueError(f"Directory non trovata: {input_dir}")
        
        # Reset statistiche totali
        self.total_stats = {'converted': 0, 'already_new': 0, 'total': 0}
        
        results = {}
        yaml_files = list(input_dir.glob(pattern)) + list(input_dir.glob("*.yml"))
        
        if not yaml_files:
            print(f"⚠️  Nessun file YAML trovato in {input_dir}")
            return results
        
        print(f"📁 Trovati {len(yaml_files)} file YAML in {input_dir}")
        print("="*60)
        
        for yaml_file in sorted(yaml_files):
            print(f"\n🔄 Processando {yaml_file.name}...")
            
            try:
                # Genera nome file output con suffisso .new.yaml
                if yaml_file.suffix.lower() == '.yml':
                    output_file = yaml_file.with_suffix('.new.yml')
                else:
                    output_file = yaml_file.with_suffix('.new.yaml')
                
                success = self.convert_file(yaml_file, output_file)
                results[str(yaml_file)] = success
                
                if success:
                    print(f"   ✅ Convertito in {output_file.name}")
                    if self.changes_log:
                        # Mostra le modifiche di questo specifico file
                        for change in self.changes_log:
                            print(f"   {change}")
                    else:
                        print("   ⚪ Nessuna modifica necessaria")
                else:
                    print(f"   ❌ Errore nella conversione")
                    
            except Exception as e:
                print(f"   ❌ Errore: {e}")
                results[str(yaml_file)] = False
        
        return results
        """Converte una stringa YAML"""
        try:
            if self.preserve_comments:
                data = self.yaml_loader.load(yaml_string)
                converted = self._convert_yaml_data(data)
                
                from io import StringIO
                output = StringIO()
                self.yaml_loader.dump(converted, output)
                return output.getvalue()
            else:
                data = yaml.safe_load(yaml_string)
                converted = self._convert_yaml_data(data)
                return yaml.dump(converted, default_flow_style=False, 
                               allow_unicode=True, sort_keys=False)
        
        except Exception as e:
            raise ValueError(f"Errore nella conversione stringa: {e}")
    
    def get_changes_report(self) -> str:
        """Restituisce un report delle modifiche effettuate"""
        if not self.changes_log:
            return "Nessuna modifica necessaria."
        
        # Conta i diversi tipi di modifiche
        converted = [log for log in self.changes_log if log.startswith("✓")]
        already_new = [log for log in self.changes_log if log.startswith("⚪")]
        
        report = "📋 Report conversione:\n"
        if converted:
            report += f"\n✅ Automazioni convertite ({len(converted)}):\n"
            report += "\n".join(converted)
        
        if already_new:
            report += f"\n\n⚪ Automazioni già aggiornate ({len(already_new)}):\n"
            report += "\n".join(already_new)
        
        report += f"\n\n📊 Totale processate: {len(self.changes_log)}"
        return report
    
    def get_summary_stats(self) -> Dict[str, int]:
        """Restituisce statistiche riassuntive"""
        converted = len([log for log in self.changes_log if log.startswith("✓")])
        already_new = len([log for log in self.changes_log if log.startswith("⚪")])
        
        return {
            'converted': converted,
            'already_new': already_new,
            'total': len(self.changes_log)
        }
    
    def get_total_stats(self) -> Dict[str, int]:
        """Restituisce statistiche totali cumulative per conversioni di directory"""
        return self.total_stats.copy()

def main():
    """Funzione principale CLI"""
    parser = argparse.ArgumentParser(
        description='Convertitore YAML Home Assistant da vecchia a nuova sintassi',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi d'uso:
  %(prog)s automation.yaml                    # Converte singolo file
  %(prog)s automation.yaml -o new_auto.yaml  # Specifica file output
  %(prog)s /path/to/automations -d            # Converte intera directory
  %(prog)s /path/to/automations -d --pattern "auto_*.yaml"  # Con pattern specifico
  %(prog)s automation.yaml --dry-run         # Anteprima modifiche
  %(prog)s automation.yaml --no-comments     # Non preserva commenti
  %(prog)s --string "alias: test..."         # Converte stringa YAML
        """
    )
    
    parser.add_argument('input_file', nargs='?', type=Path,
                       help='File o directory YAML da convertire')
    parser.add_argument('-o', '--output', type=Path,
                       help='File di output (solo per singoli file)')
    parser.add_argument('-d', '--directory', action='store_true',
                       help='Converte tutti i file YAML nella directory specificata')
    parser.add_argument('--pattern', type=str, default='*.yaml',
                       help='Pattern per file da convertire in modalità directory (default: *.yaml)')
    parser.add_argument('--no-comments', action='store_true',
                       help='Non preservare commenti e formattazione')
    parser.add_argument('--string', type=str,
                       help='Converte direttamente una stringa YAML')
    parser.add_argument('--dry-run', action='store_true',
                       help='Mostra cosa verrebbe modificato senza salvare')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    
    args = parser.parse_args()
    
    # Verifica dipendenze per preservazione commenti
    preserve_comments = not args.no_comments
    if preserve_comments:
        try:
            import ruamel.yaml
        except ImportError:
            print("⚠️  ruamel.yaml non installato. Installare con: pip install ruamel.yaml")
            print("   Procedo senza preservazione commenti...")
            preserve_comments = False
    
    # Inizializzazione convertitore
    converter = HAYamlConverter(preserve_comments=preserve_comments)
    
    # Modalità stringa
    if args.string:
        try:
            result = converter.convert_string(args.string)
            print("📤 Risultato conversione:")
            print(result)
            print(converter.get_changes_report())
            return 0
        except Exception as e:
            print(f"❌ Errore: {e}")
            return 1
    
    # Modalità directory
    if args.directory:
        if not args.input_file:
            parser.error("Specificare una directory con -d/--directory")
        
        if args.output:
            print("⚠️  Opzione -o/--output ignorata in modalità directory")
        
        print(f"📁 Conversione directory: {args.input_file}")
        print(f"🔍 Pattern: {args.pattern}")
        
        try:
            results = converter.convert_directory(args.input_file, args.pattern)
            
            # Statistiche finali
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            
            print("\n" + "="*60)
            print(f"📊 Conversione completata:")
            print(f"   ✅ File processati con successo: {successful}/{total}")
            
            if successful > 0:
                # Usa le statistiche totali cumulative invece di quelle dell'ultimo file
                total_stats = converter.get_total_stats()
                print(f"   🔄 Automazioni convertite: {total_stats['converted']}")
                print(f"   ⚪ Automazioni già aggiornate: {total_stats['already_new']}")
                print(f"   📋 Totale automazioni processate: {total_stats['total']}")
            
            # Lista eventuali errori
            failed = [file for file, success in results.items() if not success]
            if failed:
                print(f"\n❌ File con errori:")
                for file in failed:
                    print(f"   • {Path(file).name}")
            
            return 0 if successful > 0 else 1
            
        except Exception as e:
            print(f"❌ Errore nella conversione directory: {e}")
            return 1
    
    # Modalità file singolo
    if not args.input_file:
        parser.error("Specificare un file di input, directory con -d, o usare --string")
    
    if not args.input_file.exists():
        print(f"❌ File non trovato: {args.input_file}")
        return 1
    
    if args.input_file.is_dir():
        parser.error("Specificato una directory ma senza flag -d/--directory")
    
    print(f"🔄 Conversione di {args.input_file}...")
    
    # Modalità dry-run
    if args.dry_run:
        print("🔍 Modalità DRY-RUN - nessun file verrà modificato")
        try:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            converted = converter.convert_string(content)
            print("\n📋 Anteprima modifiche:")
            print(converter.get_changes_report())
            
            if converter.get_summary_stats()['converted'] > 0:
                print(f"\n💾 File che verrebbe creato: {args.output or args.input_file.with_suffix('.new.yaml')}")
            
            return 0
        except Exception as e:
            print(f"❌ Errore: {e}")
            return 1
    
    # Conversione effettiva
    if converter.convert_file(args.input_file, args.output):
        output_file = args.output or args.input_file.with_suffix('.new.yaml')
        print(f"✅ Conversione completata: {output_file}")
        print()
        print(converter.get_changes_report())
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
