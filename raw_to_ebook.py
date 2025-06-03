import os
import tempfile
import patoolib
import py7zr
from PIL import Image
from ebooklib import epub

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')

def extract_archive(archive_path, extract_to):
    if archive_path.endswith('.7z'):
        with py7zr.SevenZipFile(archive_path, mode='r') as archive:
            archive.extractall(path=extract_to)
    else:
        patoolib.extract_archive(archive_path, outdir=extract_to, verbosity=-1)

def collect_images(directory):
    images = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(IMAGE_EXTENSIONS):
                images.append(os.path.join(root, file))
    return sorted(images, key=lambda x: os.path.basename(x).lower())

def images_to_pdf(image_paths, output_pdf):
    if not image_paths:
        print("No images found.")
        return

    images = []
    for path in image_paths:
        with Image.open(path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img.copy())

    images[0].save(output_pdf, save_all=True, append_images=images[1:])
    print(f"\n✅ PDF created: {output_pdf}")

def images_to_epub(image_paths, output_epub, title="Untitled", author="Unknown"):
    if not image_paths:
        print("No images found.")
        return

    book = epub.EpubBook()
    book.set_identifier('imgbook')
    book.set_title(title)
    book.set_language('en')
    book.add_author(author)

    spine = ['nav']
    items = []

    for i, img_path in enumerate(image_paths):
        with open(img_path, 'rb') as f:
            image_data = f.read()
        img_id = f'image_{i}'
        img_item = epub.EpubItem(uid=img_id, file_name=f'images/{img_id}.jpg',
                                 media_type='image/jpeg', content=image_data)
        book.add_item(img_item)

        html = epub.EpubHtml(title=f'Page {i+1}', file_name=f'page_{i+1}.xhtml', lang='en')
        html.content = f'<html><body><img src="images/{img_id}.jpg" style="width: 100%; height: auto;" /></body></html>'
        book.add_item(html)
        spine.append(html)
        items.append(html)

    book.toc = tuple(items)
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(output_epub, book, {})
    print(f"\n✅ EPUB created: {output_epub}")

def main():
    while True:
        archive_path = input("Enter the path to the archive (zip, rar, 7z, tar, etc.): ").strip()
        if not os.path.isfile(archive_path):
            print("❌ Archive file does not exist.")
            continue

        output_format = input("Output format? Type 'pdf' or 'epub': ").strip().lower()
        if output_format not in ('pdf', 'epub'):
            print("❌ Invalid format.")
            continue

        default_output = os.path.splitext(os.path.basename(archive_path))[0] + ('.pdf' if output_format == 'pdf' else '.epub')
        output_path = input(f"Enter output file name (or press Enter to use '{default_output}'): ").strip()
        if not output_path:
            output_path = default_output

        with tempfile.TemporaryDirectory() as tempdir:
            print("\n📦 Extracting archive...")
            extract_archive(archive_path, tempdir)
            print("🖼️ Collecting images...")
            image_paths = collect_images(tempdir)

            if output_format == 'pdf':
                images_to_pdf(image_paths, output_path)
            else:
                default_title = os.path.splitext(os.path.basename(output_path))[0]
                title = input(f"Enter book title (or press Enter to use '{default_title}'): ").strip() or default_title
                author = input("Enter author name (or press Enter to use 'Unknown'): ").strip() or "Unknown"
                images_to_epub(image_paths, output_path, title, author)

        another = input("\nDo you want to convert another book? (yes/no): ").strip().lower()
        if another not in ('yes', 'y'):
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()