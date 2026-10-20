import type { GroupStatus } from "../../types";

/** What every group screen gets from `GroupSessionPage`. */
export interface GroupScreenProps {
  sessionId: string;
  /** This browser's member id: the credential for the member's own calls. */
  participantId: string;
  status: GroupStatus;
  /** Show a status an action just returned, without waiting for the stream. */
  apply: (status: GroupStatus) => void;
  /** Fetch the current status now. */
  refresh: () => Promise<void>;
}
