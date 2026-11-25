import { ButtonItem, DropdownItem, PanelSection, PanelSectionRow, Spinner, ToggleField } from "@decky/ui";
import { t, tOr } from "../i18n";
import { MUTED } from "../theme";
import type { Notice, SkipLauncherModel } from "../hooks";
import type { SettingView, Status } from "../model";

const GROUPS = ["video", "detail", "game"] as const;

const statusText = (status: Status) => tOr("code." + status.code, status.message);

function noticeText(notice: Notice | null): string | null {
  if (!notice) return null;
  switch (notice.kind) {
    case "saved":
      return t("saved");
    case "restored":
      return t("restore.done");
    case "skip-failed":
      return t("skip.failed");
    case "skip-unavailable":
      return t("skip.unavailable");
    case "status":
      return statusText(notice.result.status);
  }
}

function Note({ children }: { children: string }) {
  return <div style={{ fontSize: "0.8em", color: MUTED, lineHeight: 1.35 }}>{children}</div>;
}

function SettingRow({ setting, disabled, onChange }: { setting: SettingView; disabled: boolean; onChange: (optionId: string) => void }) {
  const label = tOr(setting.label_key, setting.label);
  const note = setting.note_key ? tOr(setting.note_key, "") : "";
  if (setting.kind === "toggle") {
    return (
      <PanelSectionRow>
        <ToggleField
          label={label}
          checked={setting.current === "on"}
          disabled={disabled || setting.current === null}
          description={setting.current === null ? t("settings.custom") : undefined}
          onChange={(on) => onChange(on ? "on" : "off")}
        />
      </PanelSectionRow>
    );
  }
  return (
    <PanelSectionRow>
      <DropdownItem
        label={label}
        description={setting.current === null ? t("settings.custom") : note || undefined}
        disabled={disabled}
        rgOptions={setting.options.map((o) => ({ data: o.id, label: tOr(o.label_key, o.label) }))}
        selectedOption={setting.current}
        onChange={(option) => onChange(String(option.data))}
      />
    </PanelSectionRow>
  );
}

/** One panel, never replaced by a loading screen: game select, the skip switch, then the launcher's settings. */
export function SkipPanel({ model }: { model: SkipLauncherModel }) {
  const { games, loaded, selected, summary, detail, skip, busy, notice } = model;
  const reading = !loaded && !games.length;
  const status = detail?.status ?? summary?.status;
  const installed = summary?.installed ?? false;
  const readable = !!detail && detail.settings.length > 0;
  const locked = busy || status?.code === "running" || status?.code === "not_ready";
  const message = noticeText(notice);

  return (
    <>
      <PanelSection>
        <PanelSectionRow>
          <DropdownItem
            layout="below"
            label={t("games.label")}
            description={
              reading ? (
                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <Spinner width={12} height={12} />
                  {t("games.reading")}
                </span>
              ) : !games.length ? (
                t("games.empty")
              ) : undefined
            }
            rgOptions={games.map((g) => ({
              data: g.appid,
              label: g.installed ? g.name : `${g.name} (${t("games.notInstalled")})`,
            }))}
            selectedOption={selected}
            disabled={!games.length}
            onChange={(option) => model.selectGame(String(option.data))}
          />
        </PanelSectionRow>
        {installed ? (
          <PanelSectionRow>
            <ToggleField
              label={t("skip.label")}
              checked={skip === true}
              disabled={busy || skip === null}
              description={skip === null ? t("skip.unavailable") : skip ? t("skip.on") : t("skip.off")}
              onChange={(on) => void model.toggleSkip(on)}
            />
          </PanelSectionRow>
        ) : null}
        {status && status.code !== "ok" ? (
          <PanelSectionRow>
            <Note>{statusText(status)}</Note>
          </PanelSectionRow>
        ) : null}
        {message ? (
          <PanelSectionRow>
            <Note>{message}</Note>
          </PanelSectionRow>
        ) : null}
      </PanelSection>

      {readable
        ? GROUPS.map((group) => {
            const rows = detail!.settings.filter((s) => s.group === group);
            return rows.length ? (
              <PanelSection key={group} title={t(("group." + group) as "group.video")}>
                {rows.map((setting) => (
                  <SettingRow
                    key={setting.id}
                    setting={setting}
                    disabled={locked}
                    onChange={(optionId) => void model.change(setting.id, optionId)}
                  />
                ))}
              </PanelSection>
            ) : null;
          })
        : null}

      {readable && detail?.changed ? (
        <PanelSection>
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={locked} description={t("restore.description")} onClick={() => void model.restore()}>
              {t("restore.label")}
            </ButtonItem>
          </PanelSectionRow>
        </PanelSection>
      ) : null}
    </>
  );
}
