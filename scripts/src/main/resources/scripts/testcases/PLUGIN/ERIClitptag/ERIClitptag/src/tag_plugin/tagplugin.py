import ast
import uuid
from litp.core.plugin import Plugin
from litp.core.task import ConfigTask
from litp.core.task import CallbackTask
from litp.core.task import RemoteExecutionTask
from litp.core.task import OrderedTaskList
from litp.plan_types.deployment_plan import deployment_plan_tags
from litp.plan_types.create_snapshot import create_snapshot_tags
from litp.plan_types.remove_snapshot import remove_snapshot_tags
from litp.plan_types.restore_snapshot import restore_snapshot_tags

from litp.core.litp_logging import LitpLogger
log = LitpLogger()


class TagPlugin(Plugin):

    #
    # dictionary of valid deployment tags mapped to model item property values;
    # these are local() to plugin class
    #
    deployment_tag_dict = {
        'ms': 'MS_TAG',
        'boot': 'BOOT_TAG',
        'node': 'NODE_TAG',
        'cluster': 'CLUSTER_TAG',
        'pre_node_cluster': 'PRE_NODE_CLUSTER_TAG'
    }

    #
    # dictionary of valid snapshot tags mapped to model item property values;
    # these are local() to plugin class
    #
    snapshot_tag_dict = {
        'validation': 'VALIDATION_TAG',
        'pre_op': 'PRE_OPERATION_TAG',
        'ms_lvm': 'LMS_LVM_VOLUME_TAG',
        'node_lvm': 'PEER_NODE_LVM_VOLUME_TAG',
        'node_vxvm': 'PEER_NODE_VXVM_VOLUME_TAG',
        'nas': 'NAS_FILESYSTEM_TAG',
        'san': 'SAN_LUN_TAG',
        'post_op': 'POST_OPERATION_TAG',
        'prep_puppet': 'PREPARE_PUPPET_TAG',
        'prep_vcs': 'PREPARE_VCS_TAG',
        'node_reboot': 'PEER_NODE_REBOOT_TAG',
        'node_power_off': 'PEER_NODE_POWER_OFF_TAG',
        'sanitisation': 'SANITISATION_TAG',
        'node_power_on': 'PEER_NODE_POWER_ON_TAG',
        'node_post_on': 'PEER_NODE_POST_POWER_ON_TAG',
        'ms_reboot': 'LMS_REBOOT_TAG'

    }

    #
    # a list of tags valid only for create and remove snapshot operations
    #
    create_remove_only = ['post_op']

    #
    # a list of tags valid only for restore snapshot operations
    #
    restore_only = [
        'prep_puppet',
        'prep_vcs',
        'node_reboot',
        'node_power_off',
        'sanitisation',
        'node_power_on',
        'node_post_on',
        'ms_reboot'
    ]

    def _get_defaults(self):
        #
        # a dictionary of default tasks and their keyword arguments if no .conf
        # file is used
        #

        default_notify_message = \
            'default_puppet_notify_unique_id_{0}'.format(uuid.uuid4())
        defaults_d = {
            'config':
                {
                    'call_type': 'notify',
                    'call_id': default_notify_message,
                },
            'callback':
                {
                    'message': 'default_callback_message'
                },
            'rpc':
                {
                    'agent': 'service',
                    'action': 'status',
                    'service': 'network'
                }
        }

        return defaults_d

    def _get_tag_object(self, plan_type, tag_parameter):
        #
        # get the tag value from the given plan_tags module by the
        # tag mapping provided in the model item property value
        #

        return getattr(plan_type, tag_parameter)

    def _get_kwargs_from_file(self, m_item):
        #
        # if a .conf file is to be used, instead of the default tasks provided,
        # get the dictionary from the <model_item.item_id>.conf
        #

        # error message to be raised in case of type() error
        error_message = "Expected type dict from {0} but got type {1} instead"
        # file name to be used <model_item.item_id>.conf
        file_name = '/usr/local/etc/tag_confs/{0}.conf'.format(
            m_item.item_id
        )
        # dictionary to store keyword arguments in
        kwargs = dict()
        try:
            # open file as context and convert string to dictionary
            with open(file_name, 'r') as context_fpath:
                kwargs = ast.literal_eval(context_fpath.read())
            # if string doesn't map to type(dict), raise type() error
            if not isinstance(kwargs, dict):
                raise TypeError(
                    error_message.format(str(kwargs), type(kwargs))
                )
            # check that dictionary keys map to dictionary values or else raise
            # type() error
            for key in kwargs.keys():
                if not isinstance(kwargs[key], dict):
                    raise TypeError(
                        error_message.format(
                            str(kwargs[key]), type(kwargs[key])
                        )
                    )

            return kwargs
        # raise error if ast.literal_eval fails to
        # evaluate contents of .conf file
        except SyntaxError as err:
            raise err
        except ValueError as err:
            raise err

    def _get_task_type(self, kwargs):
        #
        # return each task arguments in relative task type list
        #

        configs = list()
        callbacks = list()
        remoteexecs = list()

        # for each task type given as key in kwargs dictionary given, append
        # value to relative list of tasks
        for key in kwargs.keys():
            if key == 'config':
                configs.append(kwargs.pop('config'))
            elif key == 'callback':
                callbacks.append(kwargs.pop('callback'))
            elif key == 'rpc':
                remoteexecs.append(kwargs.pop('rpc'))
            else:
                error_message = "Invalid key {0} from {1}"
                raise KeyError(error_message.format(key, kwargs))

        return tuple(configs), tuple(callbacks), tuple(remoteexecs)

    def _get_config_task(self, node, model_item, plan_type, tag_p, kwargs):
        #
        # return a config task with its arguments
        #

        call_type = None
        call_id = None
        tag = self._get_tag_object(plan_type, tag_p)
        description = "A simple {0}.{1} config task for model item {2}".format(
            deployment_plan_tags.__name__, tag_p, model_item.item_id
        )
        try:
            # get puppet call_type value from kwargs dict
            call_type = kwargs.pop('call_type')
            # get puppet call_id value from kwargs dict
            call_id = '{0}_{1}'.format(kwargs.pop('call_id'), uuid.uuid4())
        # if key doesn't exist, raise key error
        except KeyError as err:
            raise err
        # append to dictionary the tag name argument
        kwargs['tag_name'] = tag

        return ConfigTask(
            node, model_item, description, call_type, call_id, **kwargs
        )

    def _get_callback_task(self, model_item, plan_type, tag_p, kwargs):
        #
        # return a callback task with its arguments
        #

        tag = self._get_tag_object(plan_type, tag_p)
        description = "A simple {0}.{1} callback task for model item {2}".\
            format(deployment_plan_tags.__name__, tag_p, model_item.item_id)
        # get the callback method name to be used for the callback task from
        # the method name, provided as a string parameter
        cb_method = getattr(self, model_item.cb_method_name)
        # append to kwargs dictionary the tag name argument
        kwargs['tag_name'] = tag

        return CallbackTask(model_item, description, cb_method, **kwargs)

    def _get_rpc_task(self, node, model_item, plan_type, tag_p, kwargs):
        #
        # return a remote execution task with its arguments
        #

        agent = None
        action = None
        tag = self._get_tag_object(plan_type, tag_p)
        description = "A simple {0}.{1} remote procedure call task for model" \
                      " item {2}".\
            format(deployment_plan_tags.__name__, tag_p, model_item.item_id)
        try:
            # get the mcollective agent from the kwargs dict
            agent = kwargs.pop('agent')
            # get the mcollective agent's action from the kwargs dict
            action = kwargs.pop('action')
        # if key doesn't exist, raise key error
        except KeyError as err:
            raise err
        kwargs['tag_name'] = tag

        return RemoteExecutionTask(
            [node], model_item, description, agent, action, **kwargs
        )

    def _model_items_to_be_ordered(self, model_items):
        #
        # if the model item specifies tasks to be ordered, then update the
        # model with a generated uuid and sort tasks by uuid
        #

        to_be_ordered = [
            m_item for m_item in model_items if m_item.ordered == 'true'
        ]
        # if model item's tasks required ordering, order them by uuid
        if to_be_ordered:
            to_be_ordered.sort(key=lambda m_item: m_item.unique_id)

            return to_be_ordered

        return None

    def _get_configuration(self, plan_type, tag_p, model_item, node):
        #
        # get the tasks configuration
        #

        _tasks = list()
        # check if the default tasks are to be used
        if model_item.defaults == 'false':
            kwargs = self._get_kwargs_from_file(model_item)
        # else use the values provided by the .conf file
        else:
            kwargs = self._get_defaults()
        configs, callbacks, remotes = self._get_task_type(kwargs)
        # return ConfigTask() for each task in ConfigTask() list
        if configs:
            for cf_kwargs in configs:
                _tasks.append(
                    self._get_config_task(
                        node, model_item, plan_type, tag_p,
                        cf_kwargs
                    )
                )
        # return CallbackTask() for each task in CallbackTask() list
        if callbacks:
            for cb_kwargs in callbacks:
                _tasks.append(
                    self._get_callback_task(
                        model_item, plan_type, tag_p, cb_kwargs
                    )
                )
        # return RemoteExecutionTask() for each task in
        # RemoteExecutionTask() list
        if remotes:
            for rpc_kwargs in remotes:
                _tasks.append(
                    self._get_rpc_task(
                        node, model_item, plan_type, tag_p, rpc_kwargs
                    )
                )

        return _tasks

    def _create_snapshot_plan(self, context_api):
        #
        # get the task configuration for create_snapshot plan
        #

        _tasks = list()
        # get all nodes from the litp model
        nodes = self._get_nodes_from_model(context_api)
        for node in nodes:
            # get tag-model-item linked to each node
            snapshot_tag_items = self._query_tag_item(node)
            if not snapshot_tag_items:
                continue
            else:
                # get snapshot plan task(s)
                # for each tag-model-item linked to nodes
                for m_item in snapshot_tag_items:
                    # check tag isn't a restore_snapshot tag only
                    if m_item.snapshot_tag not in TagPlugin.restore_only:
                        _tasks.extend(
                            self._get_snapshot_configuration(
                                create_snapshot_tags, m_item, node
                            )
                        )

        return _tasks

    def _remove_snapshot_plan(self, context_api):
        #
        # get the task configuration for remove_snapshot plan
        #

        _tasks = list()
        # get all nodes from the litp model
        nodes = self._get_nodes_from_model(context_api)
        for node in nodes:
            # get tag-model-item linked to each node
            snapshot_tag_items = self._query_tag_item(node)
            if not snapshot_tag_items:
                continue
            else:
                # get snapshot plan task(s)
                # for each tag-model-item linked to nodes
                for m_item in snapshot_tag_items:
                    # check tag isn't a restore_snapshot tag only
                    if m_item.snapshot_tag not in TagPlugin.restore_only:
                        _tasks.extend(
                            self._get_snapshot_configuration(
                                remove_snapshot_tags, m_item, node
                            )
                        )

        return _tasks

    def _restore_snapshot_plan(self, context_api):
        #
        # get the task configuration for restore_snapshot plan
        #

        _tasks = list()
        # get all nodes from the litp model
        nodes = self._get_nodes_from_model(context_api)
        for node in nodes:
            # get tag-model-item linked to each node
            snapshot_tag_items = self._query_tag_item(node)
            if not snapshot_tag_items:
                continue
            else:
                for m_item in snapshot_tag_items:
                    # check tag isn't a create_snapshot or
                    # remove_snapshot tag only
                    if m_item.snapshot_tag not in TagPlugin.create_remove_only:
                        _tasks.extend(
                            self._get_snapshot_configuration(
                                restore_snapshot_tags, m_item, node
                            )
                        )

        return _tasks

    def _get_deployment_configuration(self, model_item, node):
        #
        # get plan builder's list of tasks configuration for a standard plan
        #

        _tasks = list()
        # get the tag value from the dictionary, using the user provided
        # deployment_tag that's in the litp model
        tag_p = TagPlugin.deployment_tag_dict[model_item.deployment_tag]
        _tasks.extend(
            self._get_configuration(
                deployment_plan_tags, tag_p, model_item, node
            )
        )

        return _tasks

    def _get_snapshot_configuration(
            self, snapshot_plan_type, model_item, node):
        #
        # get plan builder's list of tasks configuration for a snapshot plan
        #

        _tasks = list()
        # get the tag value from the dictionary, using the user provided
        # snapshot_tag that's in the litp model
        tag_p = TagPlugin.snapshot_tag_dict[model_item.snapshot_tag]
        _tasks.extend(
            self._get_configuration(
                snapshot_plan_type, tag_p, model_item, node
            )
        )

        return _tasks

    def _query_ms(self, context_api):
        #
        # get the ms model item from litp model
        #

        return context_api.query('ms')[0]

    def _query_nodes(self, context_api):
        #
        # get the node model items from litp model
        #

        return context_api.query('node')

    def _get_nodes_from_model(self, context_api):
        #
        # get the list of nodes from the litp model
        #

        nodes = list()
        nodes.append(self._query_ms(context_api))
        nodes.extend(self._query_nodes(context_api))

        return nodes

    def _query_tag_item(self, context_api):
        #
        # get any tag-item from the litp model
        #

        return context_api.query('tag-model-item')

    def cb_do_something(self, callback_api, message):
        #
        # a callback method that performs logging for INFO and DEBUG messages;
        # this is the default callback method used
        #

        info_message = "TagPlugin info log message - {0}".format(message)
        debug_message = "TagPlugin debug log message - {0}:{1}".format(
            message, str(callback_api)
        )
        log.trace.info(info_message)
        log.trace.debug(debug_message)
    # if any other callback methods are required in the future, they must be
    # added to the code and then the plugin rebuilt!

    def update_model(self, context_api):
        #
        # the update_model method provided by the plugin API to update the
        # model item's uuid if the model item tasks are to be ordered
        #

        model_items = self._query_tag_item(context_api)
        nodes = self._get_nodes_from_model(context_api)
        # filter out only model items that expect tasks to be ordered
        to_be_ordered = [
            m_item for m_item in model_items if m_item.ordered == 'true'
        ]
        # if any, update the model item's uuid property
        if to_be_ordered:
            for node in nodes:
                for m_item in self._query_tag_item(node):
                    if m_item.get_source() in to_be_ordered:
                        m_item.unique_id = str(uuid.uuid4())

    def create_configuration(self, context_api):
        #
        # the create_configuration method provided by the plugin API to get the
        # list of tasks for each model item for the plan builder
        #

        tasks = list()
        ordered_tasks = list()
        # get model items of deployment-tag-item from litp model
        model_items = self._query_tag_item(context_api)
        if model_items:
            # find litp model items of tag-item that are
            # to be ordered, if any
            to_be_ordered = self._model_items_to_be_ordered(model_items)
            # get all nodes from the litp model
            nodes = self._get_nodes_from_model(context_api)
            # for each node in the model, find any
            # deployment-tag-item associated with it
            for node in nodes:
                tag_items = self._query_tag_item(node)
                # if none, move onto next node
                if not tag_items:
                    continue
                else:
                    # if any tasks to be sorted, remove them from the list of
                    # deployment-tag-item
                    if to_be_ordered:
                        tag_items[:] = [
                            m_item for m_item in tag_items
                            if m_item not in to_be_ordered
                        ]
                        # if model item is in state initial, updated or
                        # forremoval in the list of model items with tasks to
                        # be sorted, then add them to an ordered task list
                        for m_item in to_be_ordered:
                            if m_item.is_initial() or m_item.is_updated() or \
                                m_item.is_for_removal():
                                if m_item.get_source() in to_be_ordered:
                                    ordered_tasks.extend(
                                        self._get_deployment_configuration(
                                            m_item, node
                                        )
                                    )
                                    tasks.append(
                                        OrderedTaskList(m_item, ordered_tasks)
                                    )
                    # get tasks for any unsorted model items
                    for m_item in tag_items:
                        if m_item.is_initial() or m_item.is_updated() or \
                                m_item.is_for_removal():
                            tasks.extend(
                                self._get_deployment_configuration(
                                    m_item, node
                                )
                            )

        return tasks

    def create_snapshot_plan(self, context_api):
        #
        # the create_snapshot_plan method provided by the plugin API to get the
        # list of tasks for each model item for the plan builder
        #

        tasks = list()
        # check the snapshot action executed and execute
        # the right method for it
        if context_api.snapshot_action() == 'create':
            tasks.extend(self._create_snapshot_plan(context_api))
        elif context_api.snapshot_action() == 'remove':
            tasks.extend(self._remove_snapshot_plan(context_api))
        elif context_api.snapshot_action() == 'restore':
            tasks.extend(self._restore_snapshot_plan(context_api))

        return tasks
