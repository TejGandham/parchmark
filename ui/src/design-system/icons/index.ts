import { defineComponent, h, type PropType } from "vue";

export interface IconProps {
  class?: string;
  title?: string;
  ariaHidden?: boolean;
}

type SvgAttrs = Record<string, string | number | undefined>;

interface SvgNode {
  tag: string;
  attrs: SvgAttrs;
}

const iconProps = {
  class: String,
  title: String,
  ariaHidden: {
    type: Boolean as PropType<boolean | undefined>,
    default: undefined,
  },
};

function createIcon(
  name: string,
  width: number,
  height: number,
  attrs: SvgAttrs,
  nodes: SvgNode[],
) {
  return defineComponent({
    name,
    props: iconProps,
    setup(props) {
      return () => {
        const hidden = props.ariaHidden ?? !props.title;

        return h(
          "svg",
          {
            class: props.class,
            width,
            height,
            viewBox: "0 0 24 24",
            focusable: "false",
            "aria-hidden": hidden ? "true" : undefined,
            role: hidden ? undefined : "img",
            ...attrs,
          },
          [
            props.title && !hidden ? h("title", props.title) : null,
            ...nodes.map((node) => h(node.tag, node.attrs)),
          ],
        );
      };
    },
  });
}

const strokeRound = {
  fill: "none",
  stroke: "currentColor",
  "stroke-linecap": "round",
};

const strokeRoundJoin = {
  ...strokeRound,
  "stroke-linejoin": "round",
};

export const PlusIcon = createIcon(
  "PlusIcon",
  16,
  16,
  { ...strokeRound, "stroke-width": "2.2" },
  [{ tag: "path", attrs: { d: "M12 5v14M5 12h14" } }],
);

export const SearchIcon = createIcon(
  "SearchIcon",
  16,
  16,
  { fill: "none", stroke: "currentColor", "stroke-width": "2" },
  [
    { tag: "circle", attrs: { cx: "11", cy: "11", r: "7" } },
    { tag: "path", attrs: { d: "m20 20-3.2-3.2", "stroke-linecap": "round" } },
  ],
);

export const GearIcon = createIcon(
  "GearIcon",
  17,
  17,
  { fill: "none", stroke: "currentColor", "stroke-width": "1.8" },
  [
    { tag: "circle", attrs: { cx: "12", cy: "12", r: "3" } },
    {
      tag: "path",
      attrs: {
        d: "M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 6.8 19l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1.1-2.7H3a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 4.2 6.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1Z",
      },
    },
  ],
);

export const MoreIcon = createIcon(
  "MoreIcon",
  18,
  18,
  { fill: "currentColor" },
  [
    { tag: "circle", attrs: { cx: "5", cy: "12", r: "1.7" } },
    { tag: "circle", attrs: { cx: "12", cy: "12", r: "1.7" } },
    { tag: "circle", attrs: { cx: "19", cy: "12", r: "1.7" } },
  ],
);

export const EditIcon = createIcon(
  "EditIcon",
  15,
  15,
  { ...strokeRoundJoin, "stroke-width": "2" },
  [
    { tag: "path", attrs: { d: "M12 20h9" } },
    { tag: "path", attrs: { d: "M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" } },
  ],
);

export const EyeIcon = createIcon(
  "EyeIcon",
  15,
  15,
  { fill: "none", stroke: "currentColor", "stroke-width": "2" },
  [
    {
      tag: "path",
      attrs: { d: "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" },
    },
    { tag: "circle", attrs: { cx: "12", cy: "12", r: "2.7" } },
  ],
);

export const TrashIcon = createIcon(
  "TrashIcon",
  16,
  16,
  { ...strokeRoundJoin, "stroke-width": "1.9" },
  [{ tag: "path", attrs: { d: "M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14" } }],
);

export const DownloadIcon = createIcon(
  "DownloadIcon",
  16,
  16,
  { ...strokeRoundJoin, "stroke-width": "1.9" },
  [{ tag: "path", attrs: { d: "M12 3v12m0 0 4-4m-4 4-4-4M4 19h16" } }],
);

export const CopyIcon = createIcon(
  "CopyIcon",
  16,
  16,
  { ...strokeRoundJoin, "stroke-width": "1.9" },
  [
    {
      tag: "rect",
      attrs: { x: "9", y: "9", width: "11", height: "11", rx: "2" },
    },
    { tag: "path", attrs: { d: "M5 15V5a2 2 0 0 1 2-2h10" } },
  ],
);

export const XIcon = createIcon(
  "XIcon",
  14,
  14,
  { ...strokeRound, "stroke-width": "2.2" },
  [{ tag: "path", attrs: { d: "M18 6 6 18M6 6l12 12" } }],
);

export const MenuIcon = createIcon(
  "MenuIcon",
  18,
  18,
  { ...strokeRound, "stroke-width": "2" },
  [{ tag: "path", attrs: { d: "M3 6h18M3 12h18M3 18h18" } }],
);

export const SunIcon = createIcon(
  "SunIcon",
  16,
  16,
  { ...strokeRound, "stroke-width": "2" },
  [
    { tag: "circle", attrs: { cx: "12", cy: "12", r: "4" } },
    {
      tag: "path",
      attrs: {
        d: "M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4",
      },
    },
  ],
);

export const MoonIcon = createIcon(
  "MoonIcon",
  16,
  16,
  { ...strokeRoundJoin, "stroke-width": "2" },
  [
    {
      tag: "path",
      attrs: { d: "M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" },
    },
  ],
);
