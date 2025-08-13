import platform
import os
import PyInstaller.__main__

def build_web_version():
    """Build web-based standalone executable."""
    sep = ';' if platform.system() == 'Windows' else ':'
    
    opts = [
        'app.py',
        '--name=StudyCoach-Web',
        '--onefile',
        '--console',
        f'--add-data=templates{sep}templates',
        f'--add-data=static{sep}static',
        '--hidden-import=services',
        '--hidden-import=services.analyzer',
        '--hidden-import=services.ai',
        '--hidden-import=services.rag',
        '--hidden-import=services.planner',
        '--hidden-import=services.scheduler', 
        '--hidden-import=services.store',
        '--hidden-import=services.validate',
        '--hidden-import=services.webfetch',
        '--hidden-import=services.parsers',
        '--hidden-import=services.local_llm',
        '--hidden-import=services.ai_pipeline',
        '--hidden-import=flask',
        '--hidden-import=flask_cors',
        '--collect-all=sentence_transformers',
        '--collect-all=transformers', 
        '--collect-all=torch',
        '--collect-submodules=ollama',
        '--collect-submodules=openai',
        '--noconfirm',
    ]
    
    # Add icon if available
    if platform.system() == 'Windows':
        icon_path = 'static/favicon.ico'
        if os.path.exists(icon_path):
            opts.append(f'--icon={icon_path}')
    
    print(f"Building StudyCoach-Web (browser-based) for {platform.system()}...")
    PyInstaller.__main__.run(opts)


def build_desktop_version():
    """Build desktop GUI version."""
    sep = ';' if platform.system() == 'Windows' else ':'
    
    opts = [
        'desktop_app.py',
        '--name=StudyCoach',
        '--onefile',
        '--windowed' if platform.system() == 'Windows' else '--console',
        f'--add-data=templates{sep}templates',
        f'--add-data=static{sep}static',
        '--add-data=app.py{sep}.',
        '--hidden-import=services',
        '--hidden-import=services.analyzer',
        '--hidden-import=services.ai',
        '--hidden-import=services.rag',
        '--hidden-import=services.planner',
        '--hidden-import=services.scheduler', 
        '--hidden-import=services.store',
        '--hidden-import=services.validate',
        '--hidden-import=services.webfetch',
        '--hidden-import=services.parsers',
        '--hidden-import=services.local_llm',
        '--hidden-import=services.ai_pipeline',
        '--hidden-import=flask',
        '--hidden-import=flask_cors',
        '--hidden-import=tkinter',
        '--hidden-import=webview',
        '--hidden-import=requests',
        '--hidden-import=subprocess',
        '--hidden-import=threading',
        '--collect-all=sentence_transformers',
        '--collect-all=transformers', 
        '--collect-all=torch',
        '--collect-all=webview',
        '--collect-submodules=ollama',
        '--collect-submodules=openai',
        '--noconfirm',
    ]
    
    # Add icon if available
    if platform.system() == 'Windows':
        icon_path = 'static/favicon.ico'
        if os.path.exists(icon_path):
            opts.append(f'--icon={icon_path}')
    elif platform.system() == 'Darwin':  # macOS
        opts.extend([
            '--target-arch=universal2',  # Universal binary for Intel and Apple Silicon
        ])
    
    print(f"Building StudyCoach (desktop GUI) for {platform.system()}...")
    PyInstaller.__main__.run(opts)


def build(version='both'):
    """Build standalone executables."""
    print("==== Studying Coach Build System ====")
    print("This may take several minutes...")
    
    try:
        if version in ('both', 'web'):
            build_web_version()
            print("✓ Web version built successfully!")
        
        if version in ('both', 'desktop'):
            build_desktop_version()
            print("✓ Desktop version built successfully!")
        
        print("\n==== Build Complete! ====")
        print("Executables available in dist/ directory:")
        
        if platform.system() == 'Windows':
            if version in ('both', 'web'):
                print("  - StudyCoach-Web.exe (browser-based)")
            if version in ('both', 'desktop'):
                print("  - StudyCoach.exe (desktop GUI)")
        else:
            if version in ('both', 'web'):
                print("  - StudyCoach-Web (browser-based)")
            if version in ('both', 'desktop'):
                print("  - StudyCoach (desktop GUI)")
        
        print("\nUsage:")
        print("  Desktop GUI: Double-click or run the StudyCoach executable")
        print("  Web version: Run StudyCoach-Web and open http://127.0.0.1:5000")
        
    except Exception as e:
        print(f"Build failed: {e}")
        raise


if __name__ == '__main__':
    import sys
    version = sys.argv[1] if len(sys.argv) > 1 else 'both'
    if version not in ('both', 'web', 'desktop'):
        print("Usage: python build.py [both|web|desktop]")
        sys.exit(1)
    build(version)
