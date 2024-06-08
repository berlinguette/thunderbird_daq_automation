import { setupServer } from "msw/node";
import React from "react";
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { overrideHandlers } from "./fakeData";
import { getServerUrl } from "../src/api/getServerUrl";
import OverridesPanel from "../src/components/OverridesPanel";
import { fireEvent, render, screen, waitFor } from "./testUtils";
import { HttpResponse, http } from "msw";

const server = setupServer(...overrideHandlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const openPanel = () => {
  const refetchInventory = vi.fn();
  render(<OverridesPanel refetchInventory={refetchInventory} />);
  fireEvent.click(screen.getByText("Manage Overrides"));
  return refetchInventory;
}

describe("OverridesPanel", () => {
  it("can add new overrides", async () => {
    const refetchInventory = openPanel();

    fireEvent.click(screen.getByText("+ Add Override"));

    const patternInput = (await screen.findAllByDisplayValue<HTMLInputElement>("")).
      find((el) => el.placeholder === "Pattern");
    expect(patternInput).toBeInTheDocument();
    if (patternInput) patternInput.value = "ID-100";

    fireEvent.click(screen.getByText("Save"));
    await waitFor(() => expect(refetchInventory).toBeCalled());
  });
  it("can remove existing overrides", async () => {
    const refetchInventory = openPanel();
    expect(screen.getAllByText("–")).toHaveLength(2);
    fireEvent.click(screen.getAllByText("–")[0]);
    expect(screen.getAllByText("–")).toHaveLength(1);
    expect(screen.queryByText("ID-OVR")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Save"));
    await waitFor(() => expect(refetchInventory).toBeCalled());
  });
  it("will not save changes when the panel is cancelled", async () => {
    const refetchInventory = openPanel();
    expect(screen.getAllByText("–")).toHaveLength(2);
    fireEvent.click(screen.getAllByText("–")[0]);
    expect(screen.getAllByText("–")).toHaveLength(1);
    expect(screen.queryByText("ID-OVR")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Cancel"));
    await waitFor(() => expect(refetchInventory).not.toBeCalled());
  });
  it("will display error when given malformed data", async () => {
    server.use(http.get(`${getServerUrl()}/overrides`, () => {
      return HttpResponse.json([
        {
          malformed: true
        }
      ]);
    }));

    openPanel();

    expect(await screen.findByText("An error occurred when fetching data:")).toBeInTheDocument();
    expect(screen.queryByText("–")).not.toBeInTheDocument();
  });
});