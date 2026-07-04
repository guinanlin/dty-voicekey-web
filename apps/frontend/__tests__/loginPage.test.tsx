import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import Page from "@/app/login/page";
import { login } from "@/components/actions/login-action";

jest.mock("../components/actions/login-action", () => ({
  login: jest.fn(),
}));

jest.mock("../components/actions/auth-ext-action", () => ({
  phoneLogin: jest.fn(),
  sendLoginPhoneCode: jest.fn(),
}));

describe("Login Page", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  const getEmailLoginButton = () =>
    screen.getAllByRole("button", { name: /登录/i })[0];

  const getEmailInput = () => screen.getByPlaceholderText("admin@dty.com");
  const getPasswordInput = () => screen.getByLabelText("密码", { exact: true });

  it("renders the form with email and password input and submit button", () => {
    render(<Page />);

    expect(getEmailInput()).toBeInTheDocument();
    expect(getPasswordInput()).toBeInTheDocument();
    expect(getEmailLoginButton()).toBeInTheDocument();
  });

  it("calls login in successful form submission", async () => {
    (login as jest.Mock).mockResolvedValue({});

    render(<Page />);

    fireEvent.change(getEmailInput(), {
      target: { value: "testuser@example.com" },
    });
    fireEvent.change(getPasswordInput(), { target: { value: "#123176a@" } });
    fireEvent.click(getEmailLoginButton());

    await waitFor(() => {
      const formData = new FormData();
      formData.set("username", "testuser@example.com");
      formData.set("password", "#123176a@");
      expect(login).toHaveBeenCalledWith(undefined, formData);
    });
  });

  it("displays error message if login fails", async () => {
    (login as jest.Mock).mockResolvedValue({
      server_validation_error: "LOGIN_BAD_CREDENTIALS",
    });

    render(<Page />);

    fireEvent.change(getEmailInput(), {
      target: { value: "wrong@example.com" },
    });
    fireEvent.change(getPasswordInput(), { target: { value: "wrongpass" } });
    fireEvent.click(getEmailLoginButton());

    await waitFor(() => {
      expect(screen.getByText("LOGIN_BAD_CREDENTIALS")).toBeInTheDocument();
    });
  });

  it("displays server error for unexpected errors", async () => {
    (login as jest.Mock).mockResolvedValue({
      server_error: "发生了一个意外错误。请稍后再试。",
    });

    render(<Page />);

    fireEvent.change(getEmailInput(), { target: { value: "test@test.com" } });
    fireEvent.change(getPasswordInput(), { target: { value: "password123" } });
    fireEvent.click(getEmailLoginButton());

    await waitFor(() => {
      expect(
        screen.getByText("发生了一个意外错误。请稍后再试。"),
      ).toBeInTheDocument();
    });
  });
});
