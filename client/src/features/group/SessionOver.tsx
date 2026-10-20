import { useNavigate } from "react-router-dom";
import Button from "../../components/Button";
import Page from "../../components/Page";
import { ROUTES } from "../../routes";

/**
 * Shown when a group session can't continue. Results live in server memory for 30 minutes (and are
 * lost on a restart), so the only way forward is to start again.
 */
export default function SessionOver({ message }: { message: string }) {
  const navigate = useNavigate();
  return (
    <Page>
      <h1 className="title text-center">{message}</h1>
      <Button onClick={() => navigate(ROUTES.home)}>Start over</Button>
    </Page>
  );
}
