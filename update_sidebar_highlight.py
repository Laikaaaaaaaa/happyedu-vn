#!/usr/bin/env python3
"""Update all HTML files to add sidebar active item highlighting"""

import os
import re

# List of files to update
files_to_update = [
    'assessment.html',
    'chat.html',
    'conversation.html',
    'form.html',
    'forum.html',
    'prevent_violence.html',
    'profile.html',
    'quiz.html',
    'send_mail.html'
]

# CSS to add (after .sidebar-user-info span { ... })
css_addition = """
    /* Active sidebar item styling */
    .sidebar a.active,
    .sidebar button.active {
      background-color: #DBEAFE;
      color: #0F172A;
      font-weight: 700;
    }
"""

# JavaScript function to add (after updateSidebarMenu function)
js_addition = """
    // Highlight current page in sidebar
    function highlightActiveSidebarItem() {
      const currentPage = window.location.pathname.split('/').pop() || 'index.html';
      
      // Remove active class from all sidebar links
      const allLinks = document.querySelectorAll('.sidebar a, .sidebar button[onclick*="triggerSOS"]');
      allLinks.forEach(link => link.classList.remove('active'));
      
      // Add active class to current page link
      if (currentPage === 'index.html' || currentPage === '') {
        const homeLink = document.querySelector('#sidebar-home a');
        if (homeLink) homeLink.classList.add('active');
      } else if (currentPage === 'profile.html') {
        const profileLink = document.querySelector('#sidebar-profile a');
        if (profileLink) profileLink.classList.add('active');
      } else if (currentPage === 'assessment.html') {
        const assessmentLink = document.querySelector('#sidebar-assessment a');
        if (assessmentLink) assessmentLink.classList.add('active');
      } else if (currentPage === 'conversation.html' || currentPage === 'chat.html') {
        const chatLink = document.querySelector('#sidebar-chat a');
        if (chatLink) chatLink.classList.add('active');
      } else if (currentPage === 'prevent_violence.html') {
        const preventLink = document.querySelector('#sidebar-prevent a');
        if (preventLink) preventLink.classList.add('active');
      }
    }
"""

def update_file(filename):
    """Update a single HTML file"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    if not os.path.exists(filepath):
        print(f"  ❌ File not found: {filename}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Add CSS for active sidebar items (if not already present)
    if '.sidebar a.active,' not in content:
        # Find the position after .sidebar-user-info span { ... }
        pattern = r'(.sidebar-user-info span \{[^}]+\})'
        if re.search(pattern, content):
            content = re.sub(
                pattern,
                lambda m: m.group(1) + '\n' + css_addition,
                content,
                count=1
            )
            print(f"  ✓ Added CSS for active sidebar items")
        else:
            print(f"  ⚠ Could not find insertion point for CSS")
    
    # 2. Add highlightActiveSidebarItem function (if not already present)
    if 'function highlightActiveSidebarItem' not in content:
        # Find updateSidebarMenu function and add the new function after it
        pattern = r'(function updateSidebarMenu\(isLoggedIn\) \{[^}]+(?:\{[^}]*\}[^}]*)*\n    \})'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + '\n\n' + js_addition + '\n' + content[insert_pos:]
            print(f"  ✓ Added highlightActiveSidebarItem function")
        else:
            print(f"  ⚠ Could not find insertion point for JavaScript function")
    
    # 3. Update updateSidebarMenu to call highlightActiveSidebarItem
    if 'highlightActiveSidebarItem()' not in content:
        # Find the line with showItem(logoutItem); and add the function call after it
        pattern = r'(showItem\(logoutItem\);)'
        if re.search(pattern, content):
            content = re.sub(
                pattern,
                r'\1\n        \n        // Highlight active sidebar item\n        highlightActiveSidebarItem();',
                content,
                count=1
            )
            print(f"  ✓ Added highlightActiveSidebarItem() call to updateSidebarMenu")
        else:
            print(f"  ⚠ Could not find insertion point for function call")
    
    # Write back if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    else:
        print(f"  ℹ No changes needed (already updated)")
        return False

def main():
    print("Updating sidebar active item highlighting...\n")
    
    updated_count = 0
    for filename in files_to_update:
        print(f"Processing {filename}...")
        if update_file(filename):
            updated_count += 1
        print()
    
    print(f"\n✅ Updated {updated_count}/{len(files_to_update)} files")

if __name__ == '__main__':
    main()
