from aioalice.utils.helper import Helper, HelperMode, Item


class DosStates(Helper):
    mode = HelperMode.snake_case

    SELECT_HOST = Item()
    START_ATTACK = Item()
