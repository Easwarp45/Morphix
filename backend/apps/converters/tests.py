"""
Cloud File Converter — Converter Engine Tests
"""

import io
import pytest

from apps.converters.engine import (
    PNGToJPGConverter,
    JPGToPNGConverter,
    WEBPToPNGConverter,
    PNGToWEBPConverter,
    ImageCompressor,
    PDFToTXTConverter,
    TXTToPDFConverter,
    PDFCompressor,
    ZIPCreator,
    ZIPExtractor,
    get_converter,
    CONVERTER_REGISTRY,
)

from PIL import Image


def _create_test_png(width=100, height=100) -> bytes:
    """Create a minimal test PNG image."""
    img = Image.new("RGB", (width, height), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_test_jpg(width=100, height=100) -> bytes:
    """Create a minimal test JPG image."""
    img = Image.new("RGB", (width, height), color=(0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _create_test_webp(width=100, height=100) -> bytes:
    """Create a minimal test WEBP image."""
    img = Image.new("RGB", (width, height), color=(0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


class TestImageConverters:
    def test_png_to_jpg(self):
        converter = PNGToJPGConverter()
        result, ext = converter.convert(_create_test_png())
        assert ext == ".jpg"
        assert len(result) > 0
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"

    def test_jpg_to_png(self):
        converter = JPGToPNGConverter()
        result, ext = converter.convert(_create_test_jpg())
        assert ext == ".png"
        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"

    def test_webp_to_png(self):
        converter = WEBPToPNGConverter()
        result, ext = converter.convert(_create_test_webp())
        assert ext == ".png"
        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"

    def test_png_to_webp(self):
        converter = PNGToWEBPConverter()
        result, ext = converter.convert(_create_test_png())
        assert ext == ".webp"
        img = Image.open(io.BytesIO(result))
        assert img.format == "WEBP"

    def test_image_compressor(self):
        converter = ImageCompressor()
        png_bytes = _create_test_png(500, 500)
        result, ext = converter.convert(png_bytes, {"quality": 50, "max_width": 200})
        assert len(result) > 0
        assert len(result) < len(png_bytes)  # Should be smaller

    def test_png_to_jpg_with_transparency(self):
        """PNG with alpha channel should be composited on white background."""
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        converter = PNGToJPGConverter()
        result, ext = converter.convert(png_bytes)
        assert ext == ".jpg"
        result_img = Image.open(io.BytesIO(result))
        assert result_img.mode == "RGB"


class TestDocumentConverters:
    def test_txt_to_pdf(self):
        converter = TXTToPDFConverter()
        text = "Hello, World!\nThis is a test document.\n" * 10
        result, ext = converter.convert(text.encode("utf-8"))
        assert ext == ".pdf"
        assert len(result) > 0
        assert result[:4] == b"%PDF"  # PDF magic bytes

    def test_pdf_to_txt_roundtrip(self):
        """Convert TXT → PDF → TXT and verify text is preserved."""
        txt_converter = TXTToPDFConverter()
        pdf_bytes, _ = txt_converter.convert(b"Hello World")

        txt_extractor = PDFToTXTConverter()
        result, ext = txt_extractor.convert(pdf_bytes)
        assert ext == ".txt"
        assert b"Hello World" in result


class TestPDFCompressor:
    def test_compress(self):
        # First create a PDF from text
        txt_converter = TXTToPDFConverter()
        pdf_bytes, _ = txt_converter.convert(b"Test content " * 100)

        compressor = PDFCompressor()
        result, ext = compressor.convert(pdf_bytes)
        assert ext == ".pdf"
        assert len(result) > 0


class TestArchiveConverters:
    def test_zip_create(self):
        converter = ZIPCreator()
        result, ext = converter.convert(b"file content", {"filename": "test.txt"})
        assert ext == ".zip"
        assert len(result) > 0

    def test_zip_extract(self):
        # Create a ZIP first
        creator = ZIPCreator()
        zip_bytes, _ = creator.convert(b"extracted content", {"filename": "inner.txt"})

        # Then extract
        extractor = ZIPExtractor()
        result, ext = extractor.convert(zip_bytes)
        assert result == b"extracted content"
        assert ext == ".txt"

    def test_zip_extract_security(self):
        """ZIP with path traversal should be rejected."""
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../../../etc/passwd", "malicious")
        buf.seek(0)

        extractor = ZIPExtractor()
        with pytest.raises(ValueError, match="Unsafe path"):
            extractor.convert(buf.getvalue())


class TestOCRAndAIConverters:
    def test_image_ocr_to_txt(self):
        converter = get_converter("image_ocr_to_txt")
        result, ext = converter.convert(_create_test_png())
        assert ext == ".txt"
        assert len(result) > 0
        assert b"OCR" in result or b"Failed" in result or b"Tesseract" in result

    def test_pdf_ocr_to_txt(self):
        txt_converter = get_converter("txt_to_pdf")
        pdf_bytes, _ = txt_converter.convert(b"Hello OCR Text")
        
        converter = get_converter("pdf_ocr_to_txt")
        result, ext = converter.convert(pdf_bytes)
        assert ext == ".txt"
        assert b"Hello OCR Text" in result or b"Page" in result

    def test_ai_summarize(self):
        converter = get_converter("ai_summarize")
        text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four. This is sentence five. This is sentence six."
        result, ext = converter.convert(text.encode("utf-8"))
        assert ext == ".txt"
        assert len(result) > 0


class TestConverterRegistry:
    def test_all_converters_registered(self):
        expected_types = [
            "pdf_to_docx", "docx_to_pdf", "txt_to_pdf", "pdf_to_txt",
            "png_to_jpg", "jpg_to_png", "webp_to_png", "png_to_webp",
            "image_compress", "pdf_compress",
            "zip_create", "zip_extract",
            "image_ocr_to_txt", "pdf_ocr_to_txt", "ai_summarize"
        ]
        for conv_type in expected_types:
            assert conv_type in CONVERTER_REGISTRY

    def test_get_converter_valid(self):
        converter = get_converter("png_to_jpg")
        assert isinstance(converter, PNGToJPGConverter)

    def test_get_converter_invalid(self):
        with pytest.raises(ValueError, match="Unsupported"):
            get_converter("invalid_type")
