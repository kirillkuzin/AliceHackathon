from aioalice.utils.helper import Helper, HelperMode, Item


class UserStates(Helper):
    mode = HelperMode.snake_case

    SELECT_COMMAND = Item()


class DosStates(Helper):
    mode = HelperMode.snake_case

    SELECT_HOST_DOS = Item()
    START_ATTACK = Item()


class PingStates(Helper):
    mode = HelperMode.snake_case
    SELECT_HOST_PING = Item()
    START_PING = Item()
