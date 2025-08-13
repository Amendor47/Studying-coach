#!/usr/bin/env python3
"""
audit_front.py - Audit HTML/CSS/JS pour détecter les bloqueurs d'interaction
Analyse les fichiers statiques pour identifier les problèmes d'UI
"""

import os
import sys
import re
import json
from pathlib import Path
from urllib.parse import urlparse
import argparse

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠️  BeautifulSoup non disponible - analyse HTML limitée")

class FrontEndAuditor:
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.issues = []
        self.warnings = []
        self.info = []
        
    def log_issue(self, severity, file_path, line, message, suggestion=None):
        """Enregistrer un problème détecté"""
        issue = {
            "severity": severity,  # "error", "warning", "info"
            "file": str(file_path),
            "line": line,
            "message": message,
            "suggestion": suggestion
        }
        
        if severity == "error":
            self.issues.append(issue)
        elif severity == "warning":
            self.warnings.append(issue)
        else:
            self.info.append(issue)
    
    def audit_css_file(self, css_path):
        """Auditer un fichier CSS"""
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.log_issue("error", css_path, 0, f"Impossible de lire le fichier: {e}")
            return
            
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_clean = line.strip()
            
            # 1. Détecter pointer-events: none sur éléments interactifs
            if re.search(r'pointer-events\s*:\s*none', line_clean, re.IGNORECASE):
                # Chercher le sélecteur dans les lignes précédentes
                selector_context = self._find_css_selector(lines, i-1)
                interactive_selectors = ['button', '[role="button"]', '.btn', '.dropzone', 'input', 'a']
                
                if any(sel in selector_context.lower() for sel in interactive_selectors):
                    self.log_issue("error", css_path, i, 
                        f"pointer-events: none sur élément interactif: {selector_context}",
                        "Utiliser pointer-events: auto ou retirer la règle")
            
            # 2. Overlays couvrants potentiels
            overlay_keywords = ['.overlay', '.modal', '.backdrop', '.blocker', '.loader']
            if any(keyword in line_clean.lower() for keyword in overlay_keywords):
                if re.search(r'position\s*:\s*(fixed|absolute)', line_clean, re.IGNORECASE):
                    self.log_issue("warning", css_path, i, 
                        f"Overlay potentiel avec position fixed/absolute: {line_clean}",
                        "Vérifier z-index et pointer-events")
            
            # 3. Z-index très élevés
            z_index_match = re.search(r'z-index\s*:\s*(\d+)', line_clean, re.IGNORECASE)
            if z_index_match:
                z_value = int(z_index_match.group(1))
                if z_value > 9999:
                    self.log_issue("warning", css_path, i, 
                        f"Z-index très élevé ({z_value}) pouvant masquer les interactions",
                        "Utiliser z-index plus modéré")
            
            # 4. Display none sur éléments critiques
            if re.search(r'display\s*:\s*none', line_clean, re.IGNORECASE):
                selector_context = self._find_css_selector(lines, i-1)
                critical_elements = ['button', 'input', 'form', '.btn']
                
                if any(elem in selector_context.lower() for elem in critical_elements):
                    self.log_issue("warning", css_path, i, 
                        f"display: none sur élément critique: {selector_context}",
                        "Vérifier si une alternative accessible existe")
    
    def audit_html_file(self, html_path):
        """Auditer un fichier HTML"""
        if not HAS_BS4:
            self.log_issue("warning", html_path, 0, 
                "BeautifulSoup non disponible - audit HTML limité")
            return
            
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.log_issue("error", html_path, 0, f"Impossible de lire le fichier: {e}")
            return
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # 1. Boutons dans des forms sans type="button"
        forms = soup.find_all('form')
        for form in forms:
            buttons = form.find_all('button')
            for button in buttons:
                if not button.get('type'):
                    line_num = self._get_line_number(content, str(button))
                    self.log_issue("warning", html_path, line_num, 
                        "Bouton sans type dans un form (soumission par défaut)",
                        'Ajouter type="button" pour les boutons non-submit')
        
        # 2. IDs dupliqués
        ids = {}
        for element in soup.find_all(id=True):
            element_id = element['id']
            if element_id in ids:
                line_num = self._get_line_number(content, str(element))
                self.log_issue("error", html_path, line_num, 
                    f"ID dupliqué: {element_id}",
                    "Utiliser des IDs uniques")
            else:
                ids[element_id] = element
        
        # 3. Éléments disabled par défaut
        disabled_elements = soup.find_all(attrs={"disabled": True})
        for element in disabled_elements:
            if element.name in ['button', 'input']:
                line_num = self._get_line_number(content, str(element))
                self.log_issue("info", html_path, line_num, 
                    f"Élément {element.name} disabled par défaut",
                    "Vérifier si disabled doit être géré en JS")
        
        # 4. Liens et scripts potentiellement cassés
        links = soup.find_all(['link', 'script', 'img'])
        for element in links:
            src_attr = element.get('src') or element.get('href')
            if src_attr and src_attr.startswith('/static/'):
                # Vérifier si le fichier existe
                file_path = self.base_path / src_attr.lstrip('/')
                if not file_path.exists():
                    line_num = self._get_line_number(content, str(element))
                    self.log_issue("error", html_path, line_num, 
                        f"Ressource introuvable: {src_attr}",
                        "Corriger le chemin ou créer le fichier")
        
        # 5. Scripts sans defer dans le head
        head_scripts = soup.head.find_all('script', src=True) if soup.head else []
        for script in head_scripts:
            if not script.get('defer') and not script.get('async'):
                line_num = self._get_line_number(content, str(script))
                self.log_issue("info", html_path, line_num, 
                    "Script dans <head> sans defer/async",
                    "Ajouter defer ou déplacer avant </body>")
    
    def audit_js_file(self, js_path):
        """Auditer un fichier JavaScript"""
        try:
            with open(js_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.log_issue("error", js_path, 0, f"Impossible de lire le fichier: {e}")
            return
            
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_clean = line.strip()
            
            # 1. Fetch sans gestion d'erreur
            if 'fetch(' in line_clean and 'catch' not in line_clean:
                # Vérifier les lignes suivantes pour catch
                has_catch = False
                for j in range(i, min(i+5, len(lines))):
                    if 'catch' in lines[j]:
                        has_catch = True
                        break
                
                if not has_catch:
                    self.log_issue("warning", js_path, i, 
                        "Fetch sans gestion d'erreur visible",
                        "Ajouter .catch() ou try/catch")
            
            # 2. addEventListener sans vérification d'existence
            if 'addEventListener' in line_clean:
                if 'document.getElementById' in line_clean or 'querySelector' in line_clean:
                    if '?' not in line_clean and 'if (' not in line_clean:
                        self.log_issue("info", js_path, i, 
                            "addEventListener sans vérification d'existence",
                            "Vérifier que l'élément existe avant d'ajouter l'event")
    
    def _find_css_selector(self, lines, start_line):
        """Trouver le sélecteur CSS pour une ligne donnée"""
        selector = ""
        for i in range(start_line, max(0, start_line-10), -1):
            line = lines[i].strip()
            if '{' in line:
                selector = line.split('{')[0].strip()
                break
            elif line and not line.startswith('/*') and ':' not in line:
                selector = line
                break
        return selector
    
    def _get_line_number(self, content, element_str):
        """Approximer le numéro de ligne d'un élément dans le HTML"""
        lines = content.split('\n')
        # Chercher une partie unique de l'élément
        search_parts = element_str.split()[:3]  # Prendre les 3 premiers mots
        search_text = ' '.join(search_parts)
        
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 1
    
    def audit_directory(self, directory=None):
        """Auditer tous les fichiers du répertoire"""
        if directory is None:
            directory = self.base_path
        
        # Auditer les fichiers CSS
        for css_file in directory.glob('**/*.css'):
            print(f"🎨 Audit CSS: {css_file}")
            self.audit_css_file(css_file)
        
        # Auditer les fichiers HTML
        for html_file in directory.glob('**/*.html'):
            print(f"📄 Audit HTML: {html_file}")
            self.audit_html_file(html_file)
        
        # Auditer les fichiers JS
        for js_file in directory.glob('**/*.js'):
            if 'node_modules' not in str(js_file):  # Ignorer node_modules
                print(f"⚡ Audit JS: {js_file}")
                self.audit_js_file(js_file)
    
    def generate_report(self):
        """Générer le rapport d'audit"""
        total_issues = len(self.issues) + len(self.warnings) + len(self.info)
        
        print(f"\n📋 RAPPORT D'AUDIT FRONTEND")
        print("=" * 50)
        print(f"Erreurs critiques: {len(self.issues)}")
        print(f"Avertissements: {len(self.warnings)}")
        print(f"Informations: {len(self.info)}")
        print(f"Total: {total_issues} éléments détectés")
        
        # Afficher les erreurs
        if self.issues:
            print(f"\n❌ ERREURS CRITIQUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  📁 {issue['file']}:{issue['line']}")
                print(f"     🚨 {issue['message']}")
                if issue['suggestion']:
                    print(f"     💡 {issue['suggestion']}")
                print()
        
        # Afficher les avertissements
        if self.warnings:
            print(f"\n⚠️  AVERTISSEMENTS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Limiter à 10 pour la lisibilité
                print(f"  📁 {warning['file']}:{warning['line']}")
                print(f"     ⚠️  {warning['message']}")
                if warning['suggestion']:
                    print(f"     💡 {warning['suggestion']}")
                print()
            
            if len(self.warnings) > 10:
                print(f"     ... et {len(self.warnings) - 10} autres avertissements")
        
        return len(self.issues) > 0  # Retourner True si erreurs critiques


def main():
    parser = argparse.ArgumentParser(description="Audit des fichiers frontend")
    parser.add_argument("--path", default=".", help="Chemin de base à auditer")
    parser.add_argument("--json", action="store_true", help="Sortie en JSON")
    args = parser.parse_args()
    
    auditor = FrontEndAuditor(args.path)
    
    print("🔍 AUDIT FRONTEND - Détection des bloqueurs d'interaction")
    print("=" * 60)
    
    auditor.audit_directory()
    
    if args.json:
        # Sortie JSON pour traitement automatique
        result = {
            "errors": auditor.issues,
            "warnings": auditor.warnings,
            "info": auditor.info,
            "summary": {
                "errors": len(auditor.issues),
                "warnings": len(auditor.warnings),
                "info": len(auditor.info)
            }
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        has_critical_issues = auditor.generate_report()
        
        if has_critical_issues:
            print("\n🔧 ACTIONS RECOMMANDÉES:")
            print("  1. Corriger les erreurs critiques avant de continuer")
            print("  2. Exécuter tools/smoke.sh pour tester l'application")
            print("  3. Utiliser la sonde DOM (touche ~) pour debugger l'UI")
            
            sys.exit(1)
        else:
            print("\n✅ Aucune erreur critique détectée")
            sys.exit(0)


if __name__ == "__main__":
    main()