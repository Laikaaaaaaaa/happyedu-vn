#!/usr/bin/env python3
import os
import re

# Files to update with their corresponding navigation active link
files_to_update = {
    'conversation.html': 'conversation.html',  # Points to itself but for nav link it's "Trò Chuyện"
    'form.html': 'form.html',  # Special handling needed
    'forum.html': 'forum.html',  # Not in nav
    'prevent_violence.html': 'prevent_violence.html',
    'profile.html': 'profile.html',
    'quiz.html': 'quiz.html',  # Not in nav  
    'send_mail.html': 'send_mail.html',  # Not in nav
}

# Map internal file names to their nav display names and active links
nav_mapping = {
    'assessment.html': ('assessment.html', 'Đánh Giá'),
    'conversation.html': ('conversation.html', 'Trò Chuyện'),
    'prevent_violence.html': ('prevent_violence.html', 'Phòng Chống'),
    'profile.html': ('profile.html', 'Hồ Sơ'),
}

# Base CSS + Sidebar + Header structure from index.html
# These are the core navigation components that should be synced

base_directory = r"c:\Users\abc23\OneDrive\Máy tính\Student Protect"
os.chdir(base_directory)

# Read index.html to extract CSS, sidebar and header
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract style section
style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
if not style_match:
    print("Could not find style section in index.html")
    exit(1)

index_style = style_match.group(1)

# Extract sidebar (from <!-- Sidebar Overlay --> to </nav>)
sidebar_match = re.search(r'(<!-- Sidebar Overlay -->.*?</nav>)', content, re.DOTALL)
if not sidebar_match:
    print("Could not find sidebar in index.html")
    exit(1)

index_sidebar = sidebar_match.group(1)

# Extract header (from <header> to </header>)
header_match = re.search(r'(<header class="sticky top-0 z-50">.*?</header>)', content, re.DOTALL)
if not header_match:
    print("Could not find header in index.html")
    exit(1)

index_header = header_match.group(1)

# Extract script section with sidebar toggle and functions
script_match = re.search(r'(<script>\s*// Sidebar Toggle.*?</script>)', content, re.DOTALL)
if not script_match:
    print("Could not find main script in index.html")
    exit(1)

index_script = script_match.group(1)

print("✓ Successfully extracted components from index.html")
print(f"  - Style section: {len(index_style)} chars")
print(f"  - Sidebar section: {len(index_sidebar)} chars")
print(f"  - Header section: {len(index_header)} chars")
print(f"  - Script section: {len(index_script)} chars")

# Files and their active nav link
files_config = [
    ('conversation.html', 'conversation.html'),
    ('prevent_violence.html', 'prevent_violence.html'),
    ('profile.html', 'profile.html'),
    ('form.html', None),  # Not in main nav
    ('forum.html', None),  # Not in main nav
    ('quiz.html', None),  # Not in main nav
    ('send_mail.html', None),  # Not in main nav
]

for filename, nav_href in files_config:
    filepath = os.path.join(base_directory, filename)
    
    if not os.path.exists(filepath):
        print(f"⚠ Skipping {filename} - file not found")
        continue
    
    print(f"\n▶ Processing {filename}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Replace style section
        new_content = re.sub(
            r'<style>(.*?)</style>',
            f'<style>{index_style}</style>',
            file_content,
            flags=re.DOTALL
        )
        
        # Replace sidebar
        new_content = re.sub(
            r'(<!-- Sidebar Overlay -->.*?</nav>)',
            index_sidebar,
            new_content,
            flags=re.DOTALL
        )
        
        # Create custom header with proper active link
        if nav_href:
            # Start with header template without any active classes
            temp_header = re.sub(r' class="active"', '', index_header)
            # Add active class to the correct navigation link
            temp_header = temp_header.replace(
                f'<a href="{nav_href}">',
                f'<a href="{nav_href}" class="active">',
                1
            )
        else:
            # File not in main nav - keep header but remove all active classes
            temp_header = re.sub(r' class="active"', '', index_header)
        
        new_content = re.sub(
            r'<header class="sticky top-0 z-50">.*?</header>',
            temp_header,
            new_content,
            flags=re.DOTALL
        )
        
        # Replace main script section (sidebar toggle + functions)
        new_content = re.sub(
            r'<script>\s*(// Sidebar Toggle.*?</script>)',
            index_script,
            new_content,
            flags=re.DOTALL,
            count=1
        )
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✓ Updated successfully")
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

print("\n✓ All files processed!")

