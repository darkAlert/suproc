def ask_user_yes_no(question: str, logger=None):
    try:
        while True:
            user_input = input(question).strip().lower()
            if user_input == "yes" or user_input == "y":
                return True
            elif user_input == "no" or user_input == "n":
                return False
            else:
                if logger:
                    logger.debug("Invalid input. Please enter 'yes' or 'no'.")
                else:
                    print(logger)
    except KeyboardInterrupt:
        return False
    except Exception as e:
        if logger:
            logger.error(e)
        else:
            print(e)

    return False