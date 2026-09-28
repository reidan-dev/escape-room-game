"""
Interactive filter tool for data/phonebook.csv.

Loads the phonebook into a pandas DataFrame and lets you apply the
clues from data/filter_rules.yaml one at a time, so you can manually check
each elimination step before moving to the next.

Usage (from the tools/ directory):
    ../.venv/bin/python filter_phonebook.py
"""

import pandas as pd

CSV_PATH = "../data/phonebook.csv"
VOWELS = set("aeiou")


def vowel_count(s: str) -> int:
    return sum(1 for c in s.lower() if c in VOWELS)


def common_letters_ordered(a: str, b: str):
    """Letters common to both strings, in the order they appear in `a`,
    plus whether that same relative order holds in `b`."""
    a, b = a.lower(), b.lower()
    common = sorted(set(a) & set(b), key=a.index)
    positions_in_b = [b.index(c) for c in common]
    in_order = all(positions_in_b[i] <= positions_in_b[i + 1] for i in range(len(positions_in_b) - 1))
    return common, in_order


# Each rule takes the DataFrame and returns a boolean mask of rows that
# SURVIVE (i.e. match the clue, since the clue is a true fact about the answer).
RULES = [
    {
        "text": "First name is not 3 letters long.",
        "mask": lambda df: df["first_name"].str.len() != 3,
    },
    {
        "text": "First name starts with a consonant.",
        "mask": lambda df: ~df["first_name"].str[0].str.lower().isin(VOWELS),
    },
    {
        "text": "Last name has 5 or more letters.",
        "mask": lambda df: df["last_name"].str.len() >= 5,
    },
    {
        "text": "Last name does not end in a vowel.",
        "mask": lambda df: ~df["last_name"].str[-1].str.lower().isin(VOWELS),
    },
    {
        "text": "First name contains the letter A.",
        "mask": lambda df: df["first_name"].str.lower().str.contains("a"),
    },
    {
        "text": "First and last names do not start with the same letter.",
        "mask": lambda df: df["first_name"].str[0].str.lower() != df["last_name"].str[0].str.lower(),
    },
    {
        "text": "First name has more letters than the last name.",
        "mask": lambda df: df["first_name"].str.len() > df["last_name"].str.len(),
    },
    {
        "text": "First and last names have the same number of vowels.",
        "mask": lambda df: df["first_name"].apply(vowel_count) == df["last_name"].apply(vowel_count),
    },
    {
        "text": "First and last names share at least one letter.",
        "mask": lambda df: df.apply(
            lambda row: len(set(row["first_name"].lower()) & set(row["last_name"].lower())) > 0, axis=1
        ),
    },
    {
        "text": "The first and last names have exactly two letters in common, "
        "and those letters appear in the same order in both names.",
        "mask": lambda df: df.apply(
            lambda row: (
                lambda common, in_order: len(common) == 2 and in_order
            )(*common_letters_ordered(row["first_name"], row["last_name"])),
            axis=1,
        ),
    },
]


def load_phonebook() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, dtype={"phone": str})
    # "special" rows (hotline numbers, no name) aren't name-elimination
    # candidates, so they're excluded from this tool.
    return df[df["role"] != "special"].reset_index(drop=True)


def show(df: pd.DataFrame, limit: int = 20):
    # Hide the `role` column while filtering so it doesn't spoil the puzzle;
    # it's only used internally to verify the final answer.
    display_df = df.drop(columns=["role"])
    print(f"\n{len(df)} name(s) remaining.")
    if len(display_df) <= limit:
        print(display_df.to_string(index=False))
    else:
        print(display_df.head(limit).to_string(index=False))
        print(f"... ({len(display_df) - limit} more not shown)")


def print_menu(applied):
    print("\nRules:")
    for i, rule in enumerate(RULES, start=1):
        mark = "x" if (i - 1) in applied else " "
        print(f"  [{mark}] {i}. {rule['text']}")
    print("\nCommands: <rule number> = apply rule | all = apply all remaining | "
          "show = show current results | reset = start over | quit = exit")


def main():
    df = load_phonebook()
    current = df
    applied = set()

    print(f"Loaded {len(df)} entries from {CSV_PATH}.")

    while True:
        print_menu(applied)
        choice = input("\n> ").strip().lower()

        if choice in ("quit", "q", "exit"):
            break

        if choice == "reset":
            current = df
            applied = set()
            print("Reset to full phonebook.")
            continue

        if choice == "show":
            show(current)
            continue

        if choice == "all":
            for i, rule in enumerate(RULES):
                if i not in applied:
                    current = current[rule["mask"](current)]
                    applied.add(i)
            show(current)
            continue

        if choice.isdigit() and 1 <= int(choice) <= len(RULES):
            idx = int(choice) - 1
            if idx in applied:
                print("That rule is already applied. Use 'reset' to start over.")
                continue
            rule = RULES[idx]
            before = len(current)
            current = current[rule["mask"](current)]
            applied.add(idx)
            print(f"\nApplied rule {idx + 1}: {rule['text']}")
            print(f"{before} -> {len(current)} remaining.")
            show(current)
            continue

        print("Unrecognized input. Try a rule number, 'all', 'show', 'reset', or 'quit'.")

    if len(current) == 1:
        print("\nFinal answer:")
        print(current.drop(columns=["role"]).to_string(index=False))
        if current["role"].iloc[0] == "target":
            print("Matches the target row. Puzzle checks out.")
        else:
            print(f"WARNING: this survivor's role is '{current['role'].iloc[0]}', not 'target'.")
    else:
        print(f"\nExited with {len(current)} name(s) remaining.")


if __name__ == "__main__":
    main()
