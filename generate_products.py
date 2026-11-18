import re
import json

# Read Amba Agro Company.txt
with open('Amba Agro Company.txt', 'r', encoding='utf-8') as f:
    text = f.read()

matches = list(re.finditer(r'Product Name\s*:\s*(.+)', text))
blocks = []
for i in range(len(matches)):
    start = matches[i].start()
    end = matches[i+1].start() if i+1 < len(matches) else len(text)
    blocks.append((matches[i].group(1).strip(), text[start:end]))

new_products = []

for idx, (raw_name, b) in enumerate(blocks, 1):
    brand = re.sub(r'\s+', ' ', raw_name).strip()
    
    cat_match = re.search(r'Category\s*:\s*(.+)', b, re.I)
    category = cat_match.group(1).strip() if cat_match else ''
    category = re.sub(r'\s+', ' ', category)
    
    title_match = re.search(r'BIOSTIMULANTS title\s*:\s*(.+)', b, re.I)
    specification = title_match.group(1).strip() if title_match else ''
    specification = re.sub(r'\s+', ' ', specification)
    
    gaz_match = re.search(r'Gazette No\s*:\s*(.+)', b, re.I)
    gazette = gaz_match.group(1).strip() if gaz_match else ''
    gazette = re.sub(r'\s+', ' ', gazette)
    
    lines = b.splitlines()
    comp_idx = -1
    spec_idx = -1
    crop_idx = -1
    
    for i, line in enumerate(lines):
        cl = line.strip()
        if re.match(r'^Composition\b', cl, re.I):
            comp_idx = i
        elif re.match(r'^Specifications?\b', cl, re.I):
            spec_idx = i
        elif re.search(r'(^|\s|\()(crops?|name of.*crop)', cl, re.I):
            if crop_idx == -1:
                crop_idx = i
                
    comp_lines = []
    if comp_idx != -1:
        end_comp = spec_idx if spec_idx != -1 and spec_idx > comp_idx else (crop_idx if crop_idx != -1 else len(lines))
        for line in lines[comp_idx+1:end_comp]:
            cl = line.strip()
            if cl and not re.match(r'^-{5,}', cl) and not cl.lower().startswith('specifications'):
                comp_lines.append(cl)
                
    spec_lines = []
    if spec_idx != -1:
        end_spec = crop_idx if crop_idx != -1 and crop_idx > spec_idx else len(lines)
        for line in lines[spec_idx+1:end_spec]:
            cl = line.strip()
            if cl and not re.match(r'^-{5,}', cl) and not re.search(r'(crops?|name of.*crop)', cl, re.I):
                spec_lines.append(cl)
                
    crops = []
    dosage = []
    current_mode = None
    if crop_idx != -1:
        for line in lines[crop_idx:]:
            cl = line.strip()
            if not cl or re.match(r'^-{5,}', cl) or re.match(r'^\d{2,}\s*$', cl):
                continue
            crop_m = re.search(r'(?:crops?|name of (?:the )?crop)\s*[:\-]\s*(.+)', cl, re.I)
            dose_m = re.search(r'(?:doses?|dosages?)\s*[:\-]\s*(.+)', cl, re.I)
            if crop_m:
                current_mode = 'crop'
                val = crop_m.group(1).strip().rstrip(';')
                parts = re.split(r'[,;]|\band\b', val, flags=re.I)
                for p in parts:
                    p_clean = p.strip().rstrip('.')
                    if p_clean:
                        p_cap = ' '.join(w.capitalize() for w in p_clean.split())
                        if p_cap.lower() not in [c.lower() for c in crops]:
                            crops.append(p_cap)
            elif dose_m:
                current_mode = 'dose'
                val = dose_m.group(1).strip().rstrip(';')
                if val:
                    dosage.append(val)
            else:
                if current_mode == 'dose':
                    dosage.append(cl.rstrip(';'))
                elif current_mode == 'crop':
                    parts = re.split(r'[,;]|\band\b', cl, flags=re.I)
                    for p in parts:
                        p_clean = p.strip().rstrip('.')
                        if p_clean:
                            p_cap = ' '.join(w.capitalize() for w in p_clean.split())
                            if p_cap.lower() not in [c.lower() for c in crops]:
                                crops.append(p_cap)
                                
    new_products.append({
        'brand': brand,
        'displayName': brand,
        'specification': specification,
        'category': category,
        'crops': crops,
        'dosage': dosage,
        'gazette': gazette,
        'composition': comp_lines,
        'specifications': spec_lines
    })

print(f'Parsed {len(new_products)} new products.')

# Read existing productsData.js up to line 206
with open('src/productsData.js', 'r', encoding='utf-8') as f:
    old_code = f.read()

# Extract existing PRODUCTS array
match_old = re.search(r'export const PRODUCTS = \[\s*([\s\S]*?)\n\];', old_code)
if not match_old:
    raise Exception("Could not find PRODUCTS in src/productsData.js")
existing_products_str = match_old.group(1).strip().rstrip(',')

# Generate new products JS code
new_products_str_list = []
for p in new_products:
    def escape_js(s):
        return s.replace('\\', '\\\\').replace("'", "\\'")

    comp_items = ',\n'.join(f"      '{escape_js(line)}'" for line in p['composition'])
    spec_items = ',\n'.join(f"      '{escape_js(line)}'" for line in p['specifications'])
    crops_items = ', '.join(f"'{escape_js(c)}'" for c in p['crops'])
    dosage_items = ',\n'.join(f"      '{escape_js(d)}'" for d in p['dosage'])
    
    entry = f"""  {{
    brand: '{escape_js(p['brand'])}',
    displayName: '{escape_js(p['displayName'])}',
    specification: '{escape_js(p['specification'])}',
    category: '{escape_js(p['category'])}',
    crops: [{crops_items}],
    dosage: [
{dosage_items}
    ],
    gazette: '{escape_js(p['gazette'])}',
    composition: [
{comp_items}
    ],
    specifications: [
{spec_items}
    ]
  }}"""
    new_products_str_list.append(entry)

all_products_code = existing_products_str + ',\n' + ',\n'.join(new_products_str_list)

# Generate SLUG_TO_BRAND aliases
# Collect aliases for existing + new
slug_mappings = []
# Prepopulate with defaults
slug_mappings.append("  'Kalpam': 'AMBA HUMATE 49% P',")
slug_mappings.append("  'kalpam': 'AMBA HUMATE 49% P',")
slug_mappings.append("  'KALPAM': 'AMBA HUMATE 49% P',")
slug_mappings.append("  'Kalpamas': 'AMBA HUMATE 49% P',")
slug_mappings.append("  'kalpamas': 'AMBA HUMATE 49% P',")

# For all new products:
for p in new_products:
    name = p['brand']
    hyphen = name.replace(' ', '-')
    enc_hyphen = hyphen.replace('&', '%26')
    enc_space = name.replace(' ', '%20').replace('&', '%26')
    
    # Standard
    slug_mappings.append(f"  '{name}': '{name}',")
    slug_mappings.append(f"  '{name.lower()}': '{name}',")
    slug_mappings.append(f"  '{hyphen}': '{name}',")
    slug_mappings.append(f"  '{hyphen.lower()}': '{name}',")
    slug_mappings.append(f"  '{enc_space}': '{name}',")
    
    # With -new
    slug_mappings.append(f"  '{name}-new': '{name}',")
    slug_mappings.append(f"  '{name.lower()}-new': '{name}',")
    slug_mappings.append(f"  '{hyphen}-new': '{name}',")
    slug_mappings.append(f"  '{hyphen.lower()}-new': '{name}',")
    slug_mappings.append(f"  '{enc_space}-new': '{name}',")
    
    # With /new
    slug_mappings.append(f"  '{name}/new': '{name}',")
    slug_mappings.append(f"  '{name.lower()}/new': '{name}',")
    slug_mappings.append(f"  '{hyphen}/new': '{name}',")
    slug_mappings.append(f"  '{hyphen.lower()}/new': '{name}',")
    slug_mappings.append(f"  '{enc_space}/new': '{name}',")
    
    # With space new
    slug_mappings.append(f"  '{name} new': '{name}',")
    slug_mappings.append(f"  '{name.lower()} new': '{name}',")
    slug_mappings.append(f"  '{enc_space}%20new': '{name}',")

slug_mappings_code = '\n'.join(slug_mappings)

new_file_content = f"""export const GAZETTE = 'SO:3922(E), Dated: 12th September ,2024';

export const PRODUCTS = [
{all_products_code}
];

export const SLUG_TO_BRAND = {{
{slug_mappings_code}
}};

export function normalizeSlug(str) {{
  if (!str) return '';
  let s = str;
  try {{
    s = decodeURIComponent(str);
  }} catch (e) {{
    s = str;
  }}
  s = s.trim();
  s = s.replace(/^\\/+|\\/+$/g, '');
  s = s.replace(/[\\/\\-_ ]+new$/i, '');
  s = s.replace(/[-_]+/g, ' ').replace(/\\s+/g, ' ').trim().toLowerCase();
  return s;
}}

export function findProductBySlug(slug) {{
  if (!slug) return PRODUCTS[0];
  let decoded = slug;
  try {{
    decoded = decodeURIComponent(slug);
  }} catch (e) {{
    decoded = slug;
  }}
  decoded = decoded.trim();
  const rawClean = decoded.replace(/^\\/+|\\/+$/g, '');
  
  // 1. Direct alias dictionary lookup
  if (SLUG_TO_BRAND[rawClean]) {{
    const brand = SLUG_TO_BRAND[rawClean];
    const match = PRODUCTS.find(p => p && p.brand && p.brand.toUpperCase() === brand.toUpperCase());
    if (match) return match;
  }}
  if (SLUG_TO_BRAND[slug]) {{
    const brand = SLUG_TO_BRAND[slug];
    const match = PRODUCTS.find(p => p && p.brand && p.brand.toUpperCase() === brand.toUpperCase());
    if (match) return match;
  }}
  
  // 2. Exact match on brand / displayName
  const exact = PRODUCTS.find(p => 
    p && ((p.brand && p.brand.toUpperCase() === rawClean.toUpperCase()) || 
    (p.displayName && p.displayName.toUpperCase() === rawClean.toUpperCase()))
  );
  if (exact) return exact;

  // 3. Normalized match (strips -new, /new, _new, handles hyphens and spaces)
  const norm = normalizeSlug(slug);
  const foundNorm = PRODUCTS.find(p => {{
    if (!p) return false;
    const pNorm = p.brand ? normalizeSlug(p.brand) : '';
    const pDisplayNorm = p.displayName ? normalizeSlug(p.displayName) : '';
    return pNorm === norm || pDisplayNorm === norm;
  }});
  if (foundNorm) return foundNorm;

  // 4. Default fallback
  return PRODUCTS.find(p => Boolean(p)) || PRODUCTS[0];
}}

export function findProductByBrand(brand) {{
  if (!brand) return PRODUCTS[0];
  return PRODUCTS.find(p => p.brand === brand) || PRODUCTS[0];
}}
"""

with open('src/productsData.js', 'w', encoding='utf-8') as f:
    f.write(new_file_content)

print('src/productsData.js has been successfully written!')

# Save list of new product names to json for generate-qr.js
product_names = [p['brand'] for p in new_products]
with open('new_products_list.json', 'w', encoding='utf-8') as f:
    json.dump(product_names, f, indent=2)

print('new_products_list.json written with', len(product_names), 'products.')
