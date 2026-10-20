import type { MemberOut } from "../../types";

/** The members of a group session. `showProgress` adds whether each has finished voting. */
export default function MemberList({
  members,
  meName,
  showProgress = false,
}: {
  members: MemberOut[];
  meName: string;
  showProgress?: boolean;
}) {
  return (
    <ul className="card divide-y divide-line overflow-hidden">
      {members.map((member) => (
        <li key={member.name} className="flex items-center justify-between gap-3 px-4 py-3">
          <span className="text-ink">
            {member.name}
            {member.name === meName && <span className="text-muted"> (you)</span>}
            {member.is_host && (
              <span className="ml-2 rounded-full bg-accent/10 px-2 py-0.5 text-xs font-semibold text-accent">
                Host
              </span>
            )}
          </span>
          {showProgress && (
            <span
              className={`text-sm font-medium ${member.submitted ? "text-green-700" : "text-muted"}`}
            >
              {member.submitted ? "Done" : "Swiping"}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}
