import yaml

from app.models import Event, Thread


def stringifyToYaml(obj: object) -> str:
    data = obj if isinstance(obj, dict) else vars(obj)
    dumped_yaml = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
    )
    return '\n'.join('  ' + line for line in dumped_yaml.splitlines())


def event_to_prompt(event: Event) -> str:
    """Convert an event to XML tag format."""
    data = event.data if isinstance(event.data, str) else stringifyToYaml(event.data)
    return f'<{event.type.value}>\n{data}\n</{event.type.value}>'


def thread_to_prompt(thread: Thread) -> str:
    """Convert a thread to XML tag format."""
    return '\n\n'.join(event_to_prompt(event) for event in thread.events)


if __name__ == '__main__':
    import uuid
    from models import EmailMessage, EventType

    thread = Thread(ticket_id=uuid.uuid4())
    thread.events = [
        Event(
            thread_id=thread.id,
            type=EventType.EMAIL_MESSAGE,
            data=EmailMessage(user_email='123', content='''
            lskjfklasjfkdjfkajfkafk
            aksfjlksjflkds


            asfkksadlk;fjksldfjas
            kasfjsljkdl
            '''),
        )
    ]

    print(thread_to_prompt(thread))
