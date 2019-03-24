from google.appengine.ext import ndb
from user import *
from deployment import *
from visitor import *
from map_user_to_visitor import MapUserToVisitor

class RaffleRule(ndb.Model):
    deployment_key = ndb.KeyProperty()
    operator = ndb.StringProperty()
    num_checkins = ndb.IntegerProperty()
    category = ndb.StringProperty()
    url_safe_key = ndb.ComputedProperty(lambda self: self.get_url_safe_key())
    display_color = ndb.StringProperty(default="#00FFFF")

    def get_url_safe_key(self):
        if self.key:
            return self.key.urlsafe()
        return None

    def set_url_safe_key(self):
        self.put()

    def get_rule_results(self, visitor):
        checkins_query = MapUserToVisitor.query(MapUserToVisitor.visitor_key == visitor.key)
        if self.category != 'ANY':
            checkins_query = checkins_query.filter(MapUserToVisitor.category == self.category)

        count = checkins_query.count()
        if count >= self.num_checkins:
            remainder = count % self.num_checkins
            progress = int(float(remainder) / float(self.num_checkins) * 100.0)
            return int(count / self.num_checkins),progress
        else:
            progress = int(float(count) / float(self.num_checkins) * 100.0)
            return 0,progress

    @classmethod
    def get_rules_for_deployment(cls, deployment):
        rules = RaffleRule.query(RaffleRule.deployment_key == deployment.key).fetch()
        return rules

    @classmethod
    def add_raffle_rule(cls, deployment_key, operator, num_checkins, category, display_color):
        try:
            new_rule = RaffleRule(deployment_key=deployment_key, operator=operator,
                        num_checkins=num_checkins, category=category, display_color=display_color)
            new_rule.put()
            new_rule.set_url_safe_key()

            return ""
        except Exception as e:
            print str(e)
            return "Error adding raffle rule."

    @classmethod
    def process_and_rules(cls, and_rules, visitor):
        retval = None
        visitor.and_progress = []
        visitor.put()

        for and_rule in and_rules:
            res,progress = and_rule.get_rule_results(visitor)
            if retval == None:
                retval = res

            visitor.and_progress.append(progress)
            visitor.put()

            retval = min(res, retval)

        return retval

    @classmethod
    def get_raffle_entries_to_add(cls, visitor, current_count):
        deployment = visitor.deployment_key.get()
        retval = None
        or_rules = RaffleRule.query(RaffleRule.deployment_key == deployment.key,
                                 RaffleRule.operator == 'OR').order(RaffleRule.key).fetch()

        visitor.or_progress = []
        visitor.put()
        for or_rule in or_rules:
            or_result,progress = or_rule.get_rule_results(visitor)

            visitor.or_progress.append(progress)
            visitor.put()

            if retval == None:
                retval = or_result
            else:
                retval = max(or_result, retval)

        and_rules = RaffleRule.query(RaffleRule.deployment_key == deployment.key,
                                 RaffleRule.operator == 'AND').order(RaffleRule.key).fetch()

        and_result = RaffleRule.process_and_rules(and_rules=and_rules, visitor=visitor)

        if retval == None:
            retval = and_result
        total = max(and_result, retval)

        if retval == None:  # this means there are no rules, like 'Nam
            checkins_count = MapUserToVisitor.query(MapUserToVisitor.visitor_key == visitor.key).count()
            retTotal = checkins_count - current_count
        else:
            retTotal = total - current_count

        if deployment.max_raffle_entries != 0 \
            and retTotal + current_count > deployment.max_raffle_entries:
            retTotal =  deployment.max_raffle_entries - current_count

        elif deployment.max_raffle_entries != 0:
            retTotal = min(deployment.max_raffle_entries, retTotal)

        return retTotal

    @classmethod
    def edit_rule(cls, key, operator, num_checkins, category, display_color):
        rule_to_edit = ndb.Key(urlsafe=key).get()
        if rule_to_edit:
            rule_to_edit.operator = operator
            rule_to_edit.num_checkins = int(num_checkins)
            rule_to_edit.category = category
            rule_to_edit.display_color = display_color
            rule_to_edit.put()
            return ""
        else:
            return 'Cannot find request rule.'

    @classmethod
    def delete_rule(cls, key):
        try:
            rule_to_delete = ndb.Key(urlsafe=key).get()
            if rule_to_delete:
                rule_to_delete.key.delete()
                return ""
            else:
                return 'Cannot find request rule.'
        except Exception as e:
            print str(e)
            return 'Error deleting rule.'
