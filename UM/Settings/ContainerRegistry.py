# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

import os

from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase

from . import DefinitionContainer
from . import InstanceContainer
from . import ContainerStack

##  Central class to manage all Setting containers.
#
#
class ContainerRegistry:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        mime = MimeType(
            name = "application/x-uranium-definitioncontainer",
            comment = "Uranium Definition Container",
            suffixes = [ "def.json" ]
        )
        MimeTypeDatabase.addMimeType(mime)
        mime = MimeType(
            name = "application/x-uranium-instancecontainer",
            comment = "Uranium Instance Container",
            suffixes = [ "inst.cfg" ]
        )
        MimeTypeDatabase.addMimeType(mime)
        mime = MimeType(
            name = "application/x-uranium-containerstack",
            comment = "Uranium Container Stack",
            suffixes = [ "stack.cfg" ]
        )
        MimeTypeDatabase.addMimeType(mime)

        self._containers = []

        self._container_types = {
            "definition": DefinitionContainer.DefinitionContainer,
            "instance": InstanceContainer.InstanceContainer,
            "stack": ContainerStack.ContainerStack,
        }

        self._mime_type_map = {
            "application/x-uranium-definitioncontainer": DefinitionContainer.DefinitionContainer,
            "application/x-uranium-instancecontainer": InstanceContainer.InstanceContainer,
            "application/x-uranium-containerstack": ContainerStack.ContainerStack,
        }

        PluginRegistry.getInstance().addType("settings_container", self.addContainerType)

    ##  Find all DefinitionContainer objects matching certain criteria.
    #
    #   \param criteria \type{dict} A dictionary containing keys and values that need to match the metadata of the DefinitionContainer.
    def findDefinitionContainers(self, criteria):
        return self._findContainers(DefinitionContainer.DefinitionContainer, criteria)

    ##  Find all InstanceContainer objects matching certain criteria.
    #
    #   \param criteria \type{dict} A dictionary containing keys and values that need to match the metadata of the InstanceContainer.
    def findInstanceContainers(self, criteria):
        return self._findContainers(InstanceContainer.InstanceContainer, criteria)

    ##  Find all ContainerStack objects matching certain criteria.
    #
    #   \param criteria \type{dict} A dictionary containing keys and values that need to match the metadata of the ContainerStack.
    def findContainerStacks(self, criteria):
        return self._findContainers(ContainerStack.ContainerStack, criteria)

    ##  Add a container type that will be used to serialize/deserialize containers.
    #
    #   \param container An instance of the container type to add.
    def addContainerType(self, container):
        plugin_id = container.getPluginId()
        self._container_types[plugin_id] = container.__class__

        metadata = PluginRegistry.getInstance().getMetaData(plugin_id)
        self._mime_type_map[metadata["settings_container"]["mimetype"]] = container.__class_

    ##  Load all available definition containers, instance containers and container stacks.
    def load(self):
        files = Resources.getAllResourcesOfType(Resources.DefinitionContainers)
        files.extend(Resources.getAllResourcesOfType(Resources.InstanceContainers))
        files.extend(Resources.getAllResourcesOfType(Resources.ContainerStacks))

        for file_path in files:
            mime = MimeTypeDatabase.getMimeTypeForFile(file_path)
            container_type = self._mime_type_map.get(mime.name)
            container_id = mime.stripExtension(os.path.basename(file_path))

            new_container = container_type(container_id)
            with open(file_path) as f:
                new_container.deserialize(f.read())
            self._containers.append(new_container)

    def _findContainers(self, container_type, criteria):
        containers = []
        for container in self._containers:
            if container_type and not isinstance(container, container_type):
                continue

            matches_container = True
            for key, value in criteria.items():
                if key == "id":
                    if container.getId() != value:
                        matches_container = False
                    continue

                if container.getMetaDataEntry(key) != value:
                    matches_container = False

            if matches_container:
                containers.append(container)

        return containers

    ##  Get the singleton instance for this class.
    @classmethod
    def getInstance(cls):
        if not cls.__instance:
            cls.__instance = ContainerRegistry()

        return cls.__instance

    __instance = None
