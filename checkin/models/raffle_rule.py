from google.appengine.ext import ndb
from user import *
from deployment import *
from visitor import *

class RaffleRule(ndb.Model):
    deployment_key = ndb.KeyProperty()
    operator = ndb.StringProperty()
    num_checkins = ndb.IntegerProperty()
    category = ndb.StringProperty()

    def check_rule(self, visitor):
        pass

    @staticmethod
    def get_rules_for_deployment(deployment):
        rules = RaffleRule.query(RaffleRule.deployment_key == deployment.key).fetch()
        return rules

    @staticmethod
    def add_raffle_rule(deployment_key, operator, num_checkins, category):
        try:
            new_rule = RaffleRule(deployment_key=deployment_key, operator=operator,
                        num_checkins=num_checkins, category=category)
            new_rule.put()
            return new_rule
        except:
            return ""

    @staticmethod
    def process_and_rules(and_rules, visitor):
        retval = None
        for and_rule in and_rules:
            res = and_rule.check_rule(visitor)
            if retval == None:
                retval = res

            if res == 0:
                return 0
            else:
                retval = min(res, retval)
        return retval

    @staticmethod
    def get_raffle_entries_to_add(visitor, current_count):
        deployment = visitor.deployment_key.get()
        retval = 0

        if deployment.max_raffle_entries != 0 and current_count >= deployment.max_raffle_entries:
            return (deployment.max_raffle_entries - current_count)

        or_rules = RaffleRule.query(RaffleRule.deployment_key == deployment.key,
                                 RaffleRule.operator == 'OR').fetch()

        for or_rule in or_rules:
            retval = max(or_rule.check_rule(visitor), retval)

        and_rules = RaffleRule.query(RaffleRule.deployment_key == deployment.key,
                                 RaffleRule.operator == 'AND').fetch()

        and_result = RaffleRule.process_and_rules(and_rules=and_rules, visitor=visitor)
        return max(and_result, retval)
