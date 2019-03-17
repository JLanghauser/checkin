from google.appengine.ext import ndb
from user import *
from deployment import *
from visitor import *
from models.raffle_rule import RaffleRule

class RaffleEntry(ndb.Model):
    deployment_key = ndb.KeyProperty()
    visitor_key = ndb.KeyProperty()

    @staticmethod
    def add_raffle_entry(visitor):
        try:
            new_entry = RaffleEntry(deployment_key=RaffleEntry.deployment_key, visitor_key=visitor.key)
            new_entry.put()
            return new_entry
        except:
            return ""

    @staticmethod
    def remove_raffle_entries(visitor, count):
        try:
            items_to_delete = RaffleEntry.query(RaffleEntry.visitor_key == visitor.key).fetch(limit=count)
            for to_delete in items_to_delete:
                to_delete.key.delete()
            return 'DELETED'
        except:
            return ""

    @staticmethod
    def update_raffle_entries(visitor):
        current_entry_count = RaffleEntry.query(RaffleEntry.visitor_key == visitor_key).count()
        to_add = RaffleRule.get_raffle_entries_to_add(visitor, current_entry_count)

        if to_add < 0:
            reval = RaffleEntry.remove_raffle_entries(visitor, to_add)
            if retval == "":
                raise 'ERROR Updating raffle entries for visitor ' + visitor.key.id()
        else:
            for i in enumerate(to_add):
                retval = RaffleEntry.add_raffle_entry(visitor)

                if retval == "":
                    raise 'ERROR Updating raffle entries for visitor ' + visitor.key.id()
