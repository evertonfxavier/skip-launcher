import { staticClasses } from "@decky/ui";
import { definePlugin } from "@decky/api";
import { FaPlay } from "react-icons/fa";
import { Panel } from "./components";

export default definePlugin(() => ({
  name: "Skip Launcher",
  titleView: <div className={staticClasses.Title}>Skip Launcher</div>,
  content: <Panel />,
  icon: <FaPlay />,
  onDismount() {
    console.log("Skip Launcher unloading");
  },
}));
