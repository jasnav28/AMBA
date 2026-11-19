import QRCode from 'qrcode';
import PDFDocument from 'pdfkit';
import fs from 'fs';
import path from 'path';

const products = JSON.parse(fs.readFileSync('batch3_products_list.json', 'utf-8'));

const outDir = path.join(process.cwd(), 'new');
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

const generatePDF = (product) => {
  return new Promise(async (resolve, reject) => {
    // Generate URL with product name and -new in ending
    const slug = product.replace(/\s+/g, '-') + '-new';
    const url = `https://amba-opal.vercel.app/${slug}`;
    const pdfPath = path.join(outDir, `${product}.pdf`);

    try {
      // Generate QR Code image buffer (400x400 high-res)
      const qrDataUrl = await QRCode.toDataURL(url, {
        width: 400,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#ffffff'
        }
      });
      const base64Data = qrDataUrl.replace(/^data:image\/png;base64,/, '');
      const imgBuffer = Buffer.from(base64Data, 'base64');

      const doc = new PDFDocument({ size: 'A4', margin: 50 });
      const stream = fs.createWriteStream(pdfPath);
      doc.pipe(stream);

      const pageWidth = doc.page.width;
      const qrSize = 280;

      // 1. Product Name Title
      doc.moveDown(4);
      doc.fontSize(28)
         .font('Helvetica-Bold')
         .fillColor('#111827')
         .text(product, { align: 'center' });

      // 2. Centered QR Code
      doc.moveDown(2);
      const qrX = (pageWidth - qrSize) / 2;
      doc.image(imgBuffer, qrX, doc.y, { width: qrSize, height: qrSize });

      // 3. Clickable URL below QR Code
      doc.moveDown(13);
      doc.fontSize(12)
         .font('Helvetica')
         .fillColor('#0284c7')
         .text(url, { align: 'center', link: url, underline: true });

      doc.end();

      stream.on('finish', () => {
        console.log(`[OK] Generated: ${product}.pdf into folder 'new'`);
        resolve(pdfPath);
      });
      stream.on('error', (err) => {
        console.error(`[Stream Error] ${product}:`, err);
        reject(err);
      });
    } catch (err) {
      console.error(`[Error] ${product}:`, err);
      reject(err);
    }
  });
};

async function main() {
  console.log(`Generating QR code PDFs for ${products.length} products in 'new' folder...`);
  let count = 0;
  for (const product of products) {
    await generatePDF(product);
    count++;
  }
  console.log(`Successfully generated all ${count} QR code PDFs in 'new' folder.`);
}

main();
