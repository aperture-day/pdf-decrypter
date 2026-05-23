import os
import shutil
import tempfile
import unittest
import time
from pypdf import PdfReader, PdfWriter
from src.decryptor import DecryptionWorker

class TestPdfDecryption(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.input_dir)
        os.makedirs(self.output_dir)

        # Create dummy encrypted PDF
        self.encrypted_pdf_path = os.path.join(self.input_dir, "encrypted.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.encrypt("secret123")
        with open(self.encrypted_pdf_path, "wb") as f:
            writer.write(f)

        # Create dummy unencrypted PDF
        self.unencrypted_pdf_path = os.path.join(self.input_dir, "unencrypted.pdf")
        writer_un = PdfWriter()
        writer_un.add_blank_page(width=100, height=100)
        with open(self.unencrypted_pdf_path, "wb") as f:
            writer_un.write(f)

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    def test_decryption_success_with_multiple_passwords(self):
        logs = []
        progress = []
        completion_event = []

        def on_log(msg, level):
            logs.append(msg)

        def on_progress(idx, filename, status, detail):
            progress.append((filename, status, detail))

        def on_complete(success, failed, skipped):
            completion_event.append((success, failed, skipped))

        # Passwords: first is wrong, second is correct, third is wrong
        passwords = ["wrongpassword", "secret123", "anotherwrong"]

        worker = DecryptionWorker(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            passwords=passwords,
            copy_unencrypted=True,
            overwrite=True,
            on_log=on_log,
            on_progress=on_progress,
            on_complete=on_complete
        )

        # Run synchronously in main thread for testing purpose
        worker._run()

        # Check results
        self.assertEqual(len(completion_event), 1)
        success, failed, skipped = completion_event[0]
        # Both files (encrypted and unencrypted) should succeed (one by decryption, one by copy)
        self.assertEqual(success, 2)
        self.assertEqual(failed, 0)
        self.assertEqual(skipped, 0)

        # Verify output files exist and are not encrypted
        out_encrypted = os.path.join(self.output_dir, "encrypted.pdf")
        out_unencrypted = os.path.join(self.output_dir, "unencrypted.pdf")
        
        self.assertTrue(os.path.exists(out_encrypted))
        self.assertTrue(os.path.exists(out_unencrypted))

        reader_enc = PdfReader(out_encrypted)
        self.assertFalse(reader_enc.is_encrypted)

        reader_un = PdfReader(out_unencrypted)
        self.assertFalse(reader_un.is_encrypted)

    def test_decryption_failure_wrong_passwords(self):
        completion_event = []
        progress = []

        def on_complete(success, failed, skipped):
            completion_event.append((success, failed, skipped))
            
        def on_progress(idx, filename, status, detail):
            progress.append((filename, status))

        worker = DecryptionWorker(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            passwords=["wrong1", "wrong2"],
            copy_unencrypted=False,  # Skip unencrypted
            overwrite=True,
            on_complete=on_complete,
            on_progress=on_progress
        )

        worker._run()

        self.assertEqual(len(completion_event), 1)
        success, failed, skipped = completion_event[0]
        # The encrypted file fails, the unencrypted file is skipped
        self.assertEqual(success, 0)
        self.assertEqual(failed, 1)
        self.assertEqual(skipped, 1)

        # Output folder should only contain the output if it succeeded. But since it failed:
        out_encrypted = os.path.join(self.output_dir, "encrypted.pdf")
        self.assertFalse(os.path.exists(out_encrypted))

    def test_cancellation(self):
        cancel_called = []
        
        def on_cancel():
            cancel_called.append(True)

        worker = DecryptionWorker(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            passwords=["secret123"],
            copy_unencrypted=True,
            overwrite=True,
            on_cancel=on_cancel
        )
        
        # Trigger cancellation immediately
        worker.cancel()
        worker._run()

        # It should trigger the cancellation callback and abort before processing
        self.assertTrue(worker.cancel_event.is_set())
        self.assertEqual(len(cancel_called), 1)

if __name__ == '__main__':
    unittest.main()
