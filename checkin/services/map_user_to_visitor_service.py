from models.map_user_to_visitor import *
from models.raffle_entry import *

class MapUserToVisitorService:
    @staticmethod
    def get_random_visitor(deployment):
        entry_count = RaffleEntry.query(RaffleEntry.deployment_key == deployment.key).count()
        if entry_count > 0:
            random_index = randint(0, entry_count - 1)
            entries = RaffleEntry.query(RaffleEntry.deployment_key == deployment.key).order(RaffleEntry.visitor_key).fetch()

            counter = 0
            for entry in entries:
                if random_index == counter:
                    key = entry.visitor_key
                    rand_visitor = Visitor.get_by_id(key.id(),
                                                    parent=key.parent(),
                                                    app=key.app(),
                                                    namespace=key.namespace())
                    return rand_visitor.visitor_id
                counter += 1
        return None
