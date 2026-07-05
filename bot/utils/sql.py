class CheckSqlQueries:

    TRIGGER_CHECK = (
        "SELECT triggers " \
        "FROM chat_settings " \
        "WHERE id = (SELECT settings_id FROM chats WHERE <chat_id_check>)"
    )

    LAYOUT_AUTODETECT_CHECK = (
        "SELECT layout_autodetect " \
        "FROM chat_settings " \
        "WHERE id = (SELECT settings_id FROM chats WHERE <chat_id_check>)"
    )

    RP_CHECK = (
        "SELECT rp " \
        "FROM chat_settings " \
        "WHERE id = (SELECT settings_id FROM chats WHERE <chat_id_check>)"
    )