import { setupServer } from "msw/node";
import React from "react";
import {
  afterAll,
  afterEach,
  beforeAll,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { analysisStepsHandler, overrideHandlers } from "./fakeData";
import { getServerUrl } from "../src/api/getServerUrl";
import OverridesPanel from "../src/components/overrides/OverridesPanel";
import { userEvent, render, screen, waitFor, UserEvent } from "./testUtils";
import { HttpResponse, http } from "msw";

const server = setupServer(...overrideHandlers, analysisStepsHandler);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const openPanel = async (user: UserEvent) => {
  const refetchInventory = vi.fn();
  render(<OverridesPanel refetchInventory={refetchInventory} />);
  await user.click(screen.getByText("Manage Overrides"));
  return refetchInventory;
};

describe("OverridesPanel", () => {
  it("can add new overrides", async () => {
    const user = userEvent.setup();
    const refetchInventory = await openPanel(user);

    await user.click(await screen.findByText("+ Add Override"));

    // Inputs are named numerically - since fake data has 2 existing ovr, new ovr would be next id
    const patternInput = screen.getByRole("textbox", {
      name: "Pattern 2",
    });
    await user.click(patternInput);
    await user.keyboard("ID-100");

    const uncInput = screen.getByRole("textbox", {
      name: "Unconverted Data Modified Time 2",
    });
    await user.click(uncInput);
    await user.keyboard("0");

    const conInput = screen.getByRole("textbox", {
      name: "Converted Data Modified Time 2",
    });
    await user.click(conInput);
    await user.keyboard("0");

    user.click(screen.getByText("Save"));
    await waitFor(() => expect(refetchInventory).toBeCalled());
  });

  it("can remove existing overrides", async () => {
    const user = userEvent.setup();
    const refetchInventory = await openPanel(user);

    expect(await screen.findAllByText("–")).toHaveLength(2);
    await user.click(screen.getAllByText("–")[0]);
    expect(screen.getAllByText("–")).toHaveLength(1);
    expect(screen.queryByText("ID-OVR")).not.toBeInTheDocument();

    await user.click(screen.getByText("Save"));
    await waitFor(() => expect(refetchInventory).toBeCalled());
  });

  it("will not save changes when the panel is cancelled", async () => {
    const user = userEvent.setup();
    const refetchInventory = await openPanel(user);

    expect(await screen.findAllByText("–")).toHaveLength(2);
    await user.click(screen.getAllByText("–")[0]);
    expect(screen.getAllByText("–")).toHaveLength(1);
    expect(screen.queryByText("ID-OVR")).not.toBeInTheDocument();

    await user.click(screen.getByText("Cancel"));
    await waitFor(() => expect(refetchInventory).not.toBeCalled());
  });

  it("will display error when given malformed data", async () => {
    server.use(
      http.get(`${getServerUrl()}/overrides`, () => {
        return HttpResponse.json([
          {
            malformed: true,
          },
        ]);
      })
    );
    const user = userEvent.setup();
    await openPanel(user);

    expect(
      await screen.findByText("An error occurred when fetching data:")
    ).toBeInTheDocument();
    expect(screen.queryByText("–")).not.toBeInTheDocument();
  });
});
