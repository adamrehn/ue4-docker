import json
import os.path
import typing

import jsonc
import subprocess
import sys
from typing import Any
from urllib import request

common_components = [
    "Microsoft.Net.ComponentGroup.DevelopmentPrerequisites",
    "Microsoft.VisualStudio.Component.NuGet",
    "Microsoft.VisualStudio.Workload.VCTools",
    "Microsoft.VisualStudio.Workload.MSBuildTools",
]

vs2022_components = common_components + [
    "Microsoft.NetCore.Component.SDK",
]

ue5_vs_fallback_version = "17.8"


def build_vs_channel_url(vs_version: str) -> str:
    version_major = vs_version.split(".", 1)[0]
    return f"https://aka.ms/vs/{version_major}/release.ltsc.{vs_version}/channel"


class VisualStudio:
    def __init__(self, version: str, channel_url: str, components: typing.List[str]):
        self.version = version
        self.channel_url = channel_url
        self.components = sorted(set(components))

    @staticmethod
    def from_json(json_config: Any):
        # TODO: Add option to request VS2025

        try:
            vs_version = json_config["MinimumVisualStudio2022Version"]
        except KeyError:
            vs_version = ue5_vs_fallback_version

        components = (
            vs2022_components
            + json_config["VisualStudioSuggestedComponents"]
            + json_config["VisualStudio2022SuggestedComponents"]
        )

        # UE-5.4 has buggy component version
        if "Microsoft.VisualStudio.Component.Windows10SDK.22621" in components:
            components.remove("Microsoft.VisualStudio.Component.Windows10SDK.22621")
            components.append("Microsoft.VisualStudio.Component.Windows11SDK.22621")

        return VisualStudio(
            vs_version,
            build_vs_channel_url(vs_version),
            components,
        )

    def download_installer(self, installer_path: str) -> None:
        print(f"Downloading Visual Studio {self.version}...")
        # NOTE: We use the Visual Studio 2022 installer even for older Visual Studio here because the old (2017) installer now breaks
        request.urlretrieve(
            "https://aka.ms/vs/17/release/vs_buildtools.exe", installer_path
        )

    def install(self, installer_path: str) -> None:
        argv = [
            installer_path,
            "--quiet",
            "--wait",
            "--channelUri",
            self.channel_url,
            "--productId",
            "Microsoft.VisualStudio.Product.BuildTools",
            "--norestart",
            "--nocache",
            "--installPath",
            "C:/BuildTools",
            "--locale",
            "en-US",
        ]

        print(f"Installing Visual Studio {self.version}...")
        print("Components:")
        for component in self.components:
            argv.append("--add")
            argv.append(component)
            print(f" * {component}")

        sys.stdout.flush()

        subprocess.run(argv, check=True)


if __name__ == "__main__":
    windows_sdk_path = sys.argv[1]
    build_version_path = sys.argv[2]

    if os.path.exists(windows_sdk_path):
        print(f"Using Windows_SDK.json to determine VS components")
        # 5.4 or newer
        with open(sys.argv[1]) as windows_sdk_file:
            windows_sdk_json = jsonc.load(windows_sdk_file)
        vs = VisualStudio.from_json(windows_sdk_json)
    else:
        print(f"Using fallback to determine VS components")
        with open(build_version_path) as build_version_file:
            engine_version = json.load(build_version_file)
        engine_major = engine_version["MajorVersion"]
        engine_minor = engine_version["MinorVersion"]

        if engine_major == 5:
            # Assuming 5.3 or older
            vs = VisualStudio(
                ue5_vs_fallback_version,
                build_vs_channel_url(ue5_vs_fallback_version),
                vs2022_components
                + [
                    "Microsoft.Net.Component.4.6.2.TargetingPack",
                    "Microsoft.NetCore.Component.Runtime.3.1",
                    f"Microsoft.VisualStudio.Component.VC.14.38.{ue5_vs_fallback_version}.x86.x64",
                    "Microsoft.VisualStudio.Component.Windows10SDK.20348",
                ],
            )
        else:
            # Assuming 4.27
            vs = VisualStudio(
                "15",
                f"https://aka.ms/vs/15/release/channel",
                common_components
                + [
                    "Microsoft.Net.Component.4.5.TargetingPack",
                    "Microsoft.Net.Component.4.6.2.TargetingPack",
                    "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"
                    "Microsoft.VisualStudio.Component.Windows10SDK.17763",
                ],
            )

    vs_installer_path = "C:/vs_buildtools.exe"
    vs.download_installer(vs_installer_path)
    vs.install(vs_installer_path)
