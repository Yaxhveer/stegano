import argparse
import sys
from image import hide_file_in_img, extract_file_from_img
from audio import hide_file_in_audio, extract_file_from_audio

def main():
    parser = argparse.ArgumentParser(description='SecretPixel - Advanced Steganography Tool', epilog="Example commands:\n"
                                            "  Hide: python secret_pixel.py hide host.png secret.txt mypublickey.pem output.png\n"
                                            "  Extract: python secret_pixel.py extract carrier.png myprivatekey.pem [extracted.txt]",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest='command')

    # Subparser for hiding a file
    hide_parser = subparsers.add_parser('hide', help='Hide a data file inside an image or audio', epilog="Example: python secret_pixel.py hide host.png secret.txt mypublickey.pem output.png", formatter_class=argparse.RawDescriptionHelpFormatter)
    hide_parser.add_argument('type', choices=["image", "audio"], help='Type of file image or audio')
    hide_parser.add_argument('host', type=str, help='Path to the host file')
    hide_parser.add_argument('secret', type=str, help='Path to the secret file to hide')
    hide_parser.add_argument('pubkey', type=str, help='Path to the public key for encryption')
    hide_parser.add_argument('output', type=str, help='Path to the output file with embedded data')


    # Subparser for extracting a file
    extract_parser = subparsers.add_parser('extract', help='Extract a file from an image or audio', epilog="Example: python secret_pixel.py extract carrier.png  myprivatekey.pem [extracted.txt]",
                                           formatter_class=argparse.RawDescriptionHelpFormatter)
    
    extract_parser.add_argument('type', choices=["image", "audio"], help='Type of file image or audio')
    extract_parser.add_argument('carrier', type=str, help='Path to the image with embedded data')
    extract_parser.add_argument('privkey', type=str, help='Path to the private key for decryption')
    extract_parser.add_argument('passphrase', type=str, help='passphrase for decripytion')

    extract_parser.add_argument('extracted', nargs='?', type=str, default=None, help='Path to save the extracted secret file (optional, defaults to the original filename)')



    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.command == 'hide':
        if args.type == 'audio':
            hide_file_in_audio(args.host, args.secret, args.output, args.pubkey)
        else:
            hide_file_in_img(args.host, args.secret, args.output, args.pubkey)
    elif args.command == 'extract':
        # If no output file path is provided, use None to trigger default behavior
        output_file_path = args.extracted if args.extracted else None
        if args.type == 'audio':
            extract_file_from_audio(args.carrier, output_file_path, args.privkey, args.passphrase)
        else:
            extract_file_from_img(args.carrier, output_file_path, args.privkey, args.passphrase)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
