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
            new_entry = RaffleEntry(deployment_key=visitor.deployment_key, visitor_key=visitor.key)
            new_entry.put()
            return ""
        except Exception as e:
            print e
            return "Error adding raffle entry for visitor " + str(visitor.key.id)

    @staticmethod
    def remove_raffle_entries(visitor, count):
        try:
            items_to_delete = RaffleEntry.query(RaffleEntry.visitor_key == visitor.key).fetch(limit=count)
            for to_delete in items_to_delete:
                to_delete.key.delete()
            return ''
        except Exception as e:
            print str(e)
            return 'Error deleting raffle entries for ' + str(visitor.key.id())+ ':' + str(e)

    @staticmethod
    def update_raffle_entries(visitor):
        current_entry_count = RaffleEntry.query(RaffleEntry.visitor_key == visitor.key).count()
        to_add = RaffleRule.get_raffle_entries_to_add(visitor, current_entry_count)

        if to_add < 0:
            retval = RaffleEntry.remove_raffle_entries(visitor, abs(to_add))
            if retval != '':
                raise Exception(retval)
        else:
            for i in range(to_add):
                retval = RaffleEntry.add_raffle_entry(visitor)

                if retval != "":
                    raise Exception(retval)
