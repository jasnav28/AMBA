import re
import json

def parse_txt_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    matches = list(re.finditer(r'Product Name\s*:\s*(.+)', text))
    blocks = []
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        blocks.append((matches[i].group(1).strip(), text[start:end]))

    products = []
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
                    sub_parts = re.split(r'(?=\([ivx]+\))', cl)
                    for sp in sub_parts:
                        sp_clean = sp.strip()
                        if sp_clean:
                            comp_lines.append(sp_clean)
                    
        spec_lines = []
        if spec_idx != -1:
            end_spec = crop_idx if crop_idx != -1 and crop_idx > spec_idx else len(lines)
            for line in lines[spec_idx+1:end_spec]:
                cl = line.strip()
                if cl and not re.match(r'^-{5,}', cl) and not re.search(r'(crops?|name of.*crop)', cl, re.I):
                    sub_parts = re.split(r'(?=\([ivx]+\))', cl)
                    for sp in sub_parts:
                        sp_clean = sp.strip()
                        if sp_clean:
                            spec_lines.append(sp_clean)
                    
        crops = []
        dosage = []
        current_mode = None
        if crop_idx != -1:
            for line in lines[crop_idx:]:
                cl = line.strip()
                if not cl or re.match(r'^-{5,}', cl) or re.match(r'^\d{2,}\s*$', cl) or cl.startswith('* Note'):
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
                                    
        products.append({
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
    return products

# Parse batch 2 (51 products) and batch 3 (7 products)
batch2_products = parse_txt_file('Amba Agro Company.txt')
batch3_products = parse_txt_file('Amba Agro Company1.txt')

print(f'Batch 2 products count: {len(batch2_products)}')
print(f'Batch 3 products count: {len(batch3_products)}')

# Original 13 products
original_13 = """  { 
    brand: 'AMBA HUMATE 49% P',
    displayName: 'AMBA HUMATE 49% P',
    specification: 'Potassium Humate 49% (Powder)', 
    category: 'Humic Acid and Fulvic Acid and Derivatives',
    crops: ['Paddy'], 
    dosage: ['One soil application at 1 kg/ha'], 
    gazette: 'S.O. 3922(E)  12th  September, 2024', 
    composition: [
      '(i) Humic Acid per cent. by weight minimum 21', 
      '(ii) pH (1% aqueous solution) 6.0-8.0'
    ] 
  },
  {
    brand: 'AMBA HUMI 51% G',
    displayName: 'AMBA HUMI 51% G',
    specification: 'Humic Acid 51% (Granular)',
    category: 'Humic Acid and Fulvic Acid and Derivatives',
    crops: ['Green gram'],
    dosage: ['Two soil applications at 1.5 kg/ha'],
    gazette: 'S.O. 3922(E)  12th  September, 2024',
    composition: [
      '(i) Humic acid per cent. by weight minimum 51',
      '(ii) Fulvic acid per cent. by weight minimum 10',
      '(iii) pH (1% aqueous solution) 10-12',
      '(iv) Bulk Density (25°C) g/cc 0.5–0.70'
    ]
  },
  {
    brand: 'AMBA HUMI & FULI 76%P',
    displayName: 'AMBA HUMI & FULI 76%P',
    specification: 'Humic and Fulvic Acid 76% (Powder)',
    category: 'Humic Acid and Fulvic Acid and Derivatives',
    crops: ['Tomato'],
    dosage: ['Two foliar applications at 750 g/ha'],
    gazette: 'S.O. 2346(E)   26th May, 2025',
    composition: [
      '(i) Humic acid per cent. by weight, minimum (Source: Leonardite) 75',
      '(ii) Fulvic acid per cent. by weight, minimum 1',
      '(iii) Potassium by weight, minimum 6',
      '(iv) Dextrose monohydrate per cent. by weight, minimum as stabilizer 8',
      '(v) Moisture 10',
      '(vi) Total (per cent.) 100'
    ]
  },
  {
    brand: 'AMBA HUMALITE 82% P',
    displayName: 'AMBA HUMALITE 82% P',
    specification: 'Humalite 82% (Powder)',
    category: 'Humic Acid and Fulvic Acid and Derivatives',
    crops: ['Paddy'],
    dosage: [
      'Two applications: first soil application at 7 days after transplantation at 1875 g/ha',
      'Second foliar application on 28 days after transplantation at 312.5 g/ha'
    ],
    gazette: 'S.O. 3741(E)   13th August, 2025',
    composition: [
      '(i) Humalite in natural form (Canada) per cent. by weight, minimum 82',
      '(ii) Potassium hydroxide neutralizer per cent. by weight, minimum 18',
      '(iii) Total (per cent.) 100'
    ]
  },
  {
    brand: 'AMBA HUMI & FULI 85% P',
    displayName: 'AMBA HUMI & FULI 85% P',
    specification: 'Humic Acid and Fulvic Acid 85% (Powder)',
    category: 'Humic Acid and Fulvic Acid and Derivatives',
    crops: ['Tomato'],
    dosage: ['Three soil applications at 1250 g/ha'],
    gazette: 'S.O. 3741(E)  13th August, 2025',
    composition: [
      '(i) Humic acid (Source: Leonardite) per cent. by weight, minimum 70',
      '(ii) Fulvic acid per cent. by weight, minimum 15',
      '(iii) Potassium hydroxide per cent. by weight 15',
      '(iv) Total (per cent.) 100'
    ]
  },
  {
    brand: 'AMBA HUMI-40%P',
    displayName: 'AMBA HUMI-40%P',
    specification: 'Humic Acids 40% (Powder)',
    category: 'Humic Acid and Fulvic Acid and Derivatives',
    crops: ['Soybean', 'Paddy'],
    dosage: [
      'Soybean: Two soil applications at 625 g/ha',
      'Paddy: Two soil applications at 625 g/ha'
    ],
    gazette: 'S.O. 3741(E) 13th August, 2025',
    composition: [
      '(i) Humic substances (Source: Leonardite) per cent. by weight, minimum 75',
      '(ii) Potash per cent. by weight, minimum 4',
      '(iii) Precipitated Silica (Anti-caking agent) per cent. by weight, minimum 5',
      '(iv) Moisture per cent. by weight, minimum 16',
      '(v) Total (per cent.) 100'
    ]
  },
  {
    brand: 'AMBA HUMI & FULI 25%-L',
    displayName: 'AMBA HUMI & FULI 25%-L',
    specification: 'Humic and Fulvic acid 25.05% (Liquid)',
    category: 'Humic Acid and Fulvic Acid and Derivatives',
    crops: ['Tomato'],
    dosage: ['Five equal soil drench applications at 10 l/ha'],
    gazette: 'S.O. 2346E) 26th May, 2025',
    composition: [
      '(i) Humic and Fulvic acid per cent. by weight, minimum (Source: Leonardite) 25.05',
      '(ii) Water per cent. by weight 74.95',
      '(iii) Total (per cent.) 100'
    ]
  },
  {
    brand: 'AMBA MIXTURE OF HAV& B',
    displayName: 'AMBA MIXTURE OF HAV& B',
    specification: 'Mixture of Humic Acid, Amino Acid, Vitamins and Bio-chemicals (Powder)',
    category: 'Mixed Formulation',
    crops: ['Okra'],
    dosage: ['Two soil applications at 250 g/ha'],
    gazette: 'S.O. 3922(E).  12th  September, 2024',
    composition: [
      '(i) Humic Acid per cent. by weight, minimum 30',
      '(ii) Amino Acid (Glycine) per cent. by weight, minimum 7',
      '(iii) Myoinositol per cent. by weight, minimum 2',
      '(iv) Vitamin C per cent by weight, minimum 12.0',
      '(v) Vitamin E per cent by weight, minimum 0.2',
      '(vi) pH (1% aqueous solution) 5.0–6.5',
      '(vii) Total organic carbon per cent by weight, minimum 25'
    ]
  },
  {
    brand: 'AMBA AMINO20%L',
    displayName: 'AMBA AMINO20%L',
    specification: 'Protein hydrolysate (Amino acids 20%) (Plant source) (Liquid)',
    category: 'Protein Hydrolysates and Amino Acids',
    crops: ['Soybean'],
    dosage: ['Two foliar applications at 2 l/ha'],
    gazette: 'S.O. 2346E) 26th May, 2025',
    composition: [
      '(i) Protein hydrolysate (Microbial fermentation) per cent. by weight, minimum',
      'a. Sugarbeet molasses 87.1',
      'b. Corn/Wheat glucose syrups 12.4',
      '(ii) Octhilinone as preservatives per cent. by weight, minimum 0.3',
      '(iii) Polysiloxanes as antifoam agent per cent. by weight, minimum 0.2',
      '(iv) Total (per cent.) 100'
    ]
  },
  {
    brand: 'AMBA PLANT 27%P',
    displayName: 'AMBA PLANT 27%P',
    specification: 'Protein hydrolysate 27% (Plant Source) (Powder)',
    category: 'Protein Hydrolysates and Amino Acids',
    crops: ['Paddy'],
    dosage: ['Seed treatment before sowing at 3.0 g/kg seed'],
    gazette: 'S.O. 2346(E)   26th May, 2025',
    composition: [
      '(i) Soy flour per cent. by weight, minimum 27',
      '(ii) Enzymes [Protease 2% (400U/g) + Amylase 1% (80U/g)] per cent. by weight, minimum 3',
      '(iii) Diatomaceous Earth powder per cent. by weight, maximum 70',
      '(iv) Total (per cent.) 100'
    ]
  },
  {
    brand: 'AMBA AGRO S-A-A-8.3% GR',
    displayName: 'AMBA AGRO S-A-A-8.3% GR',
    specification: 'S- Abscisic acid (8.3%) (Granule)',
    category: 'Anti-transpirant',
    crops: ['Wheat', 'Rice'],
    dosage: ['One foliar application at 62.5 g/ha for both wheat and rice'],
    gazette: 'S.O. 3742(E)   13th August, 2025',
    composition: [
      '(i) S- Abscisic acid per cent. by weight, minimum 8.3',
      '(ii) Malic acid per cent. by weight, minimum QS',
      '(iii) Total (per cent.) 100'
    ]
  },
  {
    brand: 'AMBA BROMO',
    displayName: 'AMBA BROMO',
    specification: '2- Bromo- (1H)- Indole- 3 Carboxaldehyde 1 ppm (Liquid)',
    category: 'Biochemicals',
    crops: ['Tomato'],
    dosage: ['Seed treatment at 1 ppm formulation'],
    gazette: 'S.O. 2346E)  26th May, 2025',
    composition: [
      '(i) 2- Bromo- (1H)- Indole- 3 Carboxaldehyde per cent. by weight, minimum 0.0001',
      '(ii) Water per cent. by weight QS',
      '(iii) Total (per cent.) 100'
    ]
  },
  {
    brand: 'AMBA SEAWEED 35%P',
    displayName: 'AMBA SEAWEED 35%P',
    specification: 'Seaweed(Sargassum wightii) extract 35% (Powder)',
    category: 'Seaweed Extract',
    crops: ['Chilli'],
    dosage: ['Three foliar applications at 200 g/ha'],
    gazette: 'S.O. 3742(E)   13th August, 2025',
    composition: [
      '(i) Seaweed (Sargassum wightii) extract per cent. by weight, minimum 35',
      '(ii) Bentonite per cent. by weight QS',
      '(iii) Total (per cent.) 100'
    ]
  }"""

all_added_products = batch2_products + batch3_products
print(f'Total added products: {len(all_added_products)}')

def escape_js(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")

new_products_str_list = []
for p in all_added_products:
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

all_products_code = original_13.strip().rstrip(',') + ',\n' + ',\n'.join(new_products_str_list)

# Generate SLUG_TO_BRAND
slug_mappings = []
slug_mappings.append("  'Kalpam': 'AMBA HUMATE 49% P',")
slug_mappings.append("  'kalpam': 'AMBA HUMATE 49% P',")
slug_mappings.append("  'KALPAM': 'AMBA HUMATE 49% P',")
slug_mappings.append("  'Kalpamas': 'AMBA HUMATE 49% P',")
slug_mappings.append("  'kalpamas': 'AMBA HUMATE 49% P',")

for p in all_added_products:
    name = p['brand']
    hyphen = name.replace(' ', '-')
    enc_hyphen = hyphen.replace('&', '%26')
    enc_space = name.replace(' ', '%20').replace('&', '%26')
    
    slug_mappings.append(f"  '{name}': '{name}',")
    slug_mappings.append(f"  '{name.lower()}': '{name}',")
    slug_mappings.append(f"  '{hyphen}': '{name}',")
    slug_mappings.append(f"  '{hyphen.lower()}': '{name}',")
    slug_mappings.append(f"  '{enc_space}': '{name}',")
    
    slug_mappings.append(f"  '{name}-new': '{name}',")
    slug_mappings.append(f"  '{name.lower()}-new': '{name}',")
    slug_mappings.append(f"  '{hyphen}-new': '{name}',")
    slug_mappings.append(f"  '{hyphen.lower()}-new': '{name}',")
    slug_mappings.append(f"  '{enc_space}-new': '{name}',")
    
    slug_mappings.append(f"  '{name}/new': '{name}',")
    slug_mappings.append(f"  '{name.lower()}/new': '{name}',")
    slug_mappings.append(f"  '{hyphen}/new': '{name}',")
    slug_mappings.append(f"  '{hyphen.lower()}/new': '{name}',")
    slug_mappings.append(f"  '{enc_space}/new': '{name}',")
    
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

print('Updated src/productsData.js with all 71 products.')

# Save batch 3 product names to batch3_products_list.json
batch3_names = [p['brand'] for p in batch3_products]
with open('batch3_products_list.json', 'w', encoding='utf-8') as f:
    json.dump(batch3_names, f, indent=2)

print('batch3_products_list.json saved with 7 products:', batch3_names)
