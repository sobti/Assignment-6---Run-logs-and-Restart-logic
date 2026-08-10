import { FunctionComponent, h } from "preact";
import { FeatherProps } from "preact-feather/dist/types";
import { cx } from "../../util/cx";
import { focusable } from "../styles";

export const ToolbarButton: FunctionComponent<{
    label: string;
    icon: FunctionComponent<FeatherProps>;
    onClick?: () => void;
    pressed?: boolean;
    expanded?: boolean;
}> = ({ label, icon, onClick, pressed, expanded }) => {
    const isActive = pressed === true || expanded === true;
    const Icon = icon;
    return (
        <button
            onClick={onClick}
            className={cx(
                "bg-gray-900",
                "border-black",
                "flex",
                "h-12",
                "hover:bg-gray-800",
                "hover:border-gray-900",
                "hover:shadow-2xl",
                "items-center",
                "justify-center",
                "rounded-full",
                "shadow-xl",
                "w-12",
                focusable,
                {
                    "hover:text-blue-400": isActive,
                    "hover:text-gray-400": !isActive,
                    "text-blue-500": isActive,
                    "text-gray-500": !isActive,
                },
            )}
        >
            <Icon aria-hidden="true" />
            <span className={cx("sr-only")}>{label}</span>
        </button>
    );
};

ToolbarButton.displayName = "ToolbarButton";
