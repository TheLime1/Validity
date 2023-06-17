import poe
import os


def remove_bad_tokens():
    poe_tokens_file = ("poe_tokens.txt")
    token_to_test_file = ("token_to_test.txt")
    valid_tokens = []
    bad_tokens = []

    # Check for bad tokens in poe_tokens.txt
    try:
        with open(poe_tokens_file, 'r') as f:
            poe_tokens = f.read().splitlines()

        for token in poe_tokens:
            try:
                client = poe.Client(token)
                valid_tokens.append(token)
                print(f"Valid token: {token}")

            except RuntimeError:
                bad_tokens.append(token)
                print(f"Removing bad token: {token}")

        with open(poe_tokens_file, 'w') as f:
            # Write the valid tokens to the poe_tokens.txt file
            f.write('\n'.join(valid_tokens))

    except FileNotFoundError:
        print("poe_tokens.txt file not found.")

    # Append valid tokens from token_to_test.txt
    try:
        with open(token_to_test_file, 'r') as f:
            test_tokens = f.read().splitlines()

        new_valid_tokens = []

        for token in test_tokens:
            try:
                client = poe.Client(token)
                if token not in valid_tokens:
                    new_valid_tokens.append(token)
                    print(f"Valid token: {token}")

            except RuntimeError:
                bad_tokens.append(token)
                print(f"Removing bad token: {token}")

        with open(poe_tokens_file, 'a') as f:
            # Append only new valid tokens to the poe_tokens.txt file
            f.write('\n' + '\n'.join(new_valid_tokens))

        # Delete the token_to_test.txt file
        os.remove(token_to_test_file)

    except FileNotFoundError:
        print("token_to_test.txt file not found.")

    print("Valid tokens:")
    print(valid_tokens)

    print("Bad tokens:")
    print(bad_tokens)


# Usage example
remove_bad_tokens()
