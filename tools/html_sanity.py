#!/usr/bin/env python3
"""
html_sanity.py - Validation de balisage HTML et vérification de cohérence
Utilise BeautifulSoup pour analyser la structure HTML
"""

import os
import sys
from pathlib import Path
import re
import argparse

try:
    from bs4 import BeautifulSoup, Comment
    HAS_BS4 = True
except ImportError:
    print("❌ BeautifulSoup4 requis: pip install beautifulsoup4")
    sys.exit(1)

class HTMLSanityChecker:
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.errors = []
        self.warnings = []
        self.info = []
    
    def log_issue(self, severity, file_path, element, message, suggestion=None):
        """Enregistrer un problème détecté"""
        issue = {
            "severity": severity,
            "file": str(file_path),
            "element": str(element)[:100] if element else "N/A",
            "message": message,
            "suggestion": suggestion
        }
        
        if severity == "error":
            self.errors.append(issue)
        elif severity == "warning":
            self.warnings.append(issue)
        else:
            self.info.append(issue)
    
    def check_html_file(self, html_path):
        """Vérifier un fichier HTML"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.log_issue("error", html_path, None, f"Impossible de lire le fichier: {e}")
            return
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
        except Exception as e:
            self.log_issue("error", html_path, None, f"Erreur parsing HTML: {e}")
            return
        
        print(f"📄 Vérification HTML: {html_path}")
        
        # 1. Structure de base
        self._check_basic_structure(html_path, soup)
        
        # 2. IDs et classes
        self._check_ids_and_classes(html_path, soup)
        
        # 3. Formulaires et éléments interactifs
        self._check_interactive_elements(html_path, soup)
        
        # 4. Ressources (liens, images, scripts)
        self._check_resources(html_path, soup)
        
        # 5. Accessibilité de base
        self._check_accessibility(html_path, soup)
        
        # 6. Validité sémantique
        self._check_semantic_validity(html_path, soup)
    
    def _check_basic_structure(self, html_path, soup):
        """Vérifier la structure HTML de base"""
        # Lire le contenu pour vérifier le DOCTYPE
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            content = ""
            
        # DOCTYPE
        if not content.strip().startswith('<!DOCTYPE html>'):
            if not any(str(item).startswith('<!DOCTYPE') for item in soup.contents):
                self.log_issue("warning", html_path, None, 
                    "DOCTYPE HTML5 manquant", 
                    "Ajouter <!DOCTYPE html> en début de fichier")
        
        # Élément html avec lang
        html_elem = soup.find('html')
        if html_elem and not html_elem.get('lang'):
            self.log_issue("warning", html_path, html_elem,
                "Attribut lang manquant sur <html>",
                'Ajouter lang="fr" ou langue appropriée')
        
        # Head et title
        head = soup.find('head')
        if not head:
            self.log_issue("error", html_path, None, "<head> manquant")
        else:
            title = head.find('title')
            if not title:
                self.log_issue("error", html_path, head, "<title> manquant dans <head>")
            elif not title.string or title.string.strip() == "":
                self.log_issue("warning", html_path, title, "Titre vide")
        
        # Meta charset
        charset_meta = soup.find('meta', attrs={'charset': True})
        if not charset_meta:
            self.log_issue("warning", html_path, head,
                "Meta charset manquant",
                'Ajouter <meta charset="UTF-8">')
        
        # Meta viewport pour responsive
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if not viewport_meta:
            self.log_issue("info", html_path, head,
                "Meta viewport manquant pour design responsive",
                'Ajouter <meta name="viewport" content="width=device-width, initial-scale=1">')
    
    def _check_ids_and_classes(self, html_path, soup):
        """Vérifier les IDs et classes"""
        # IDs dupliqués
        ids = {}
        for element in soup.find_all(id=True):
            element_id = element['id']
            if element_id in ids:
                self.log_issue("error", html_path, element,
                    f"ID dupliqué: {element_id}",
                    "Utiliser des IDs uniques")
            else:
                ids[element_id] = element
        
        # IDs vides
        empty_ids = soup.find_all(id="")
        for element in empty_ids:
            self.log_issue("warning", html_path, element,
                "ID vide", "Supprimer l'attribut id vide ou lui donner une valeur")
        
        # Classes vides
        empty_classes = soup.find_all(attrs={"class": ""})
        for element in empty_classes:
            self.log_issue("info", html_path, element,
                "Classe vide", "Supprimer l'attribut class vide")
    
    def _check_interactive_elements(self, html_path, soup):
        """Vérifier les éléments interactifs"""
        # Boutons dans les formulaires
        forms = soup.find_all('form')
        for form in forms:
            buttons = form.find_all('button')
            for button in buttons:
                button_type = button.get('type')
                if not button_type:
                    self.log_issue("warning", html_path, button,
                        "Bouton dans form sans attribut type (soumission par défaut)",
                        'Ajouter type="button" ou type="submit"')
        
        # Labels et inputs
        labels = soup.find_all('label')
        for label in labels:
            label_for = label.get('for')
            if label_for:
                # Vérifier que l'input correspondant existe
                target_input = soup.find(id=label_for)
                if not target_input:
                    self.log_issue("error", html_path, label,
                        f"Label pointe vers un élément inexistant: {label_for}",
                        "Corriger l'ID cible ou créer l'élément manquant")
        
        # Inputs sans labels
        inputs = soup.find_all(['input', 'textarea', 'select'])
        for inp in inputs:
            inp_id = inp.get('id')
            inp_type = inp.get('type', 'text')
            
            # Ignorer les inputs cachés et boutons
            if inp_type in ['hidden', 'submit', 'reset', 'button']:
                continue
            
            if inp_id:
                # Chercher un label correspondant
                label = soup.find('label', attrs={'for': inp_id})
                if not label:
                    # Chercher un label parent
                    parent_label = inp.find_parent('label')
                    if not parent_label:
                        self.log_issue("warning", html_path, inp,
                            f"Input sans label associé: {inp_id}",
                            "Ajouter un <label> approprié")
        
        # Éléments disabled par défaut
        disabled_elements = soup.find_all(attrs={"disabled": True})
        for element in disabled_elements:
            self.log_issue("info", html_path, element,
                f"Élément {element.name} disabled par défaut",
                "Vérifier si disabled doit être géré dynamiquement")
    
    def _check_resources(self, html_path, soup):
        """Vérifier les ressources (CSS, JS, images)"""
        # Links CSS
        css_links = soup.find_all('link', rel='stylesheet')
        for link in css_links:
            href = link.get('href')
            if href and href.startswith('/static/'):
                # Vérifier si le fichier existe
                file_path = self.base_path / href.lstrip('/')
                if not file_path.exists():
                    self.log_issue("error", html_path, link,
                        f"Fichier CSS introuvable: {href}",
                        "Corriger le chemin ou créer le fichier")
        
        # Scripts
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            src = script.get('src')
            if src and src.startswith('/static/'):
                file_path = self.base_path / src.lstrip('/')
                if not file_path.exists():
                    self.log_issue("error", html_path, script,
                        f"Fichier JS introuvable: {src}",
                        "Corriger le chemin ou créer le fichier")
        
        # Images
        images = soup.find_all('img')
        for img in images:
            src = img.get('src')
            alt = img.get('alt')
            
            if not alt and alt != "":  # alt="" est valide pour images décoratives
                self.log_issue("warning", html_path, img,
                    "Image sans attribut alt",
                    "Ajouter un texte alternatif ou alt=\"\" si décorative")
            
            if src and src.startswith('/static/'):
                file_path = self.base_path / src.lstrip('/')
                if not file_path.exists():
                    self.log_issue("warning", html_path, img,
                        f"Image introuvable: {src}",
                        "Corriger le chemin ou ajouter l'image")
    
    def _check_accessibility(self, html_path, soup):
        """Vérifications d'accessibilité de base"""
        # Liens sans texte
        links = soup.find_all('a')
        for link in links:
            # Vérifier s'il y a du texte visible
            text_content = link.get_text(strip=True)
            aria_label = link.get('aria-label')
            title = link.get('title')
            
            if not text_content and not aria_label and not title:
                # Vérifier s'il y a des images avec alt
                images = link.find_all('img')
                has_alt = any(img.get('alt') for img in images)
                
                if not has_alt:
                    self.log_issue("warning", html_path, link,
                        "Lien sans texte accessible",
                        "Ajouter du texte, aria-label, ou alt sur les images")
        
        # Headings - ordre hiérarchique
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if headings:
            prev_level = 0
            for heading in headings:
                current_level = int(heading.name[1])
                if prev_level > 0 and current_level > prev_level + 1:
                    self.log_issue("warning", html_path, heading,
                        f"Saut de niveau de heading: {heading.name} après h{prev_level}",
                        "Respecter la hiérarchie des headings")
                prev_level = current_level
    
    def _check_semantic_validity(self, html_path, soup):
        """Vérifications de validité sémantique"""
        # Scripts dans head sans defer/async
        head = soup.find('head')
        if head:
            head_scripts = head.find_all('script', src=True)
            for script in head_scripts:
                if not script.get('defer') and not script.get('async'):
                    self.log_issue("info", html_path, script,
                        "Script dans <head> sans defer/async",
                        "Ajouter defer ou déplacer avant </body>")
        
        # Balises obsolètes
        obsolete_tags = ['center', 'font', 'marquee', 'blink', 'big', 'small', 'tt']
        for tag in obsolete_tags:
            elements = soup.find_all(tag)
            for element in elements:
                self.log_issue("warning", html_path, element,
                    f"Balise obsolète: <{tag}>",
                    "Utiliser CSS pour le style")
        
        # Tables sans structure
        tables = soup.find_all('table')
        for table in tables:
            if not table.find(['th', 'thead', 'tbody', 'tfoot']):
                self.log_issue("info", html_path, table,
                    "Table sans structure sémantique",
                    "Ajouter <th>, <thead>, <tbody> si approprié")
    
    def check_directory(self, directory=None):
        """Vérifier tous les fichiers HTML du répertoire"""
        if directory is None:
            directory = self.base_path
        
        html_files = list(directory.glob('**/*.html'))
        
        if not html_files:
            print("⚠️  Aucun fichier HTML trouvé")
            return
        
        for html_file in html_files:
            self.check_html_file(html_file)
    
    def generate_report(self):
        """Générer le rapport de vérification"""
        total_issues = len(self.errors) + len(self.warnings) + len(self.info)
        
        print(f"\n📋 RAPPORT DE VALIDATION HTML")
        print("=" * 50)
        print(f"Erreurs: {len(self.errors)}")
        print(f"Avertissements: {len(self.warnings)}")
        print(f"Informations: {len(self.info)}")
        print(f"Total: {total_issues} éléments détectés")
        
        # Afficher les erreurs
        if self.errors:
            print(f"\n❌ ERREURS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  📁 {error['file']}")
                print(f"     🚨 {error['message']}")
                if error['suggestion']:
                    print(f"     💡 {error['suggestion']}")
                if error['element'] != "N/A":
                    print(f"     🔍 Élément: {error['element']}")
                print()
        
        # Afficher les avertissements
        if self.warnings:
            print(f"\n⚠️  AVERTISSEMENTS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Limiter l'affichage
                print(f"  📁 {warning['file']}")
                print(f"     ⚠️  {warning['message']}")
                if warning['suggestion']:
                    print(f"     💡 {warning['suggestion']}")
                print()
            
            if len(self.warnings) > 10:
                print(f"     ... et {len(self.warnings) - 10} autres avertissements")
        
        return len(self.errors) > 0

def main():
    parser = argparse.ArgumentParser(description="Validation HTML et vérification de cohérence")
    parser.add_argument("--path", default=".", help="Chemin de base à vérifier")
    parser.add_argument("--file", help="Fichier HTML spécifique à vérifier")
    args = parser.parse_args()
    
    checker = HTMLSanityChecker(args.path)
    
    print("📋 VALIDATION HTML - Vérification de cohérence")
    print("=" * 50)
    
    if args.file:
        file_path = Path(args.file)
        if file_path.exists():
            checker.check_html_file(file_path)
        else:
            print(f"❌ Fichier non trouvé: {args.file}")
            sys.exit(1)
    else:
        checker.check_directory()
    
    has_errors = checker.generate_report()
    
    if has_errors:
        print("\n🔧 ACTIONS RECOMMANDÉES:")
        print("  1. Corriger les erreurs détectées")
        print("  2. Valider avec un validateur HTML externe")
        print("  3. Tester l'accessibilité avec des outils dédiés")
        sys.exit(1)
    else:
        print("\n✅ Validation HTML terminée sans erreur critique")
        sys.exit(0)

if __name__ == "__main__":
    main()