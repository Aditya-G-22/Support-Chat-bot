import pandas as pd
from dataclasses import dataclass

TAG_COLUMNS = ["tag_1", "tag_2", "tag_3", "tag_4", "tag_5", "tag_6", "tag_7", "tag_8"]

@dataclass
class Ticket:
    subject: str
    body: str
    answer: str
    language: str
    queue: str
    type: str
    priority: str
    tags: list[str]


def load_tickets(csv_path: str) -> list[Ticket]:
    df = pd.read_csv(csv_path)

    df = df.dropna(subset=["body", "answer"])

    tickets = []
    for _, row in df.iterrows():
        tags = [row[col] for col in TAG_COLUMNS if pd.notna(row[col])]

        subject = row["subject"] if pd.notna(row["subject"]) else ""

        ticket = Ticket(
            subject=subject,
            body=row["body"],
            answer=row["answer"],
            language=row["language"],
            queue=row["queue"],
            type=row["type"],
            priority=row["priority"],
            tags=tags,
        )
        tickets.append(ticket)

    return tickets


# if __name__ == "__main__":
#     tickets = load_tickets("data/dataset-tickets-multi-lang-4-20k.csv")
#     print(f"Loaded {len(tickets)} tickets")
#     print(tickets[0])
#     empty_subjects = [t for t in tickets if t.subject == ""]
#     print(f"Tickets with empty subject: {len(empty_subjects)}")