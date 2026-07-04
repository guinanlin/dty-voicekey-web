import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import Page from "@/app/register/page";
import { registerWithVerificationCode } from "@/components/actions/auth-ext-action";

jest.mock("../components/actions/auth-ext-action", () => ({
  registerWithVerificationCode: jest.fn(),
  sendRegisterEmailCode: jest.fn(),
}));

describe("Register Page", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders the form with email, code, password input and submit button", () => {
    render(<Page />);

    expect(screen.getByLabelText(/邮箱/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/验证码/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^密码$/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /注册/i })).toBeInTheDocument();
  });

  it("displays success message on successful form submission", async () => {
    (registerWithVerificationCode as jest.Mock).mockResolvedValue({});

    render(<Page />);

    const emailInput = screen.getByLabelText(/邮箱/i);
    const codeInput = screen.getByLabelText(/验证码/i);
    const passwordInput = screen.getByLabelText(/^密码$/i);
    const submitButton = screen.getByRole("button", { name: /注册/i });

    fireEvent.change(emailInput, { target: { value: "testuser@example.com" } });
    fireEvent.change(codeInput, { target: { value: "123456" } });
    fireEvent.change(passwordInput, { target: { value: "@1231231%a" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      const formData = new FormData();
      formData.set("email", "testuser@example.com");
      formData.set("code", "123456");
      formData.set("password", "@1231231%a");
      expect(registerWithVerificationCode).toHaveBeenCalledWith(
        undefined,
        formData,
      );
    });
  });

  it("displays server validation error if register fails", async () => {
    (registerWithVerificationCode as jest.Mock).mockResolvedValue({
      server_validation_error: "User already exists",
    });

    render(<Page />);

    const emailInput = screen.getByLabelText(/邮箱/i);
    const codeInput = screen.getByLabelText(/验证码/i);
    const passwordInput = screen.getByLabelText(/^密码$/i);
    const submitButton = screen.getByRole("button", { name: /注册/i });

    fireEvent.change(emailInput, { target: { value: "already@already.com" } });
    fireEvent.change(codeInput, { target: { value: "123456" } });
    fireEvent.change(passwordInput, { target: { value: "@1231231%a" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("User already exists")).toBeInTheDocument();
    });
  });

  it("displays server error for unexpected errors", async () => {
    (registerWithVerificationCode as jest.Mock).mockResolvedValue({
      server_error: "发生了一个意外错误。请稍后再试。",
    });

    render(<Page />);

    const emailInput = screen.getByLabelText(/邮箱/i);
    const codeInput = screen.getByLabelText(/验证码/i);
    const passwordInput = screen.getByLabelText(/^密码$/i);
    const submitButton = screen.getByRole("button", { name: /注册/i });

    fireEvent.change(emailInput, { target: { value: "test@test.com" } });
    fireEvent.change(codeInput, { target: { value: "123456" } });
    fireEvent.change(passwordInput, { target: { value: "@1231231%a" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("发生了一个意外错误。请稍后再试。"),
      ).toBeInTheDocument();
    });

    const formData = new FormData();
    formData.set("email", "test@test.com");
    formData.set("code", "123456");
    formData.set("password", "@1231231%a");
    expect(registerWithVerificationCode).toHaveBeenCalledWith(
      undefined,
      formData,
    );
  });

  it("displays validation errors if password and email are invalid", async () => {
    (registerWithVerificationCode as jest.Mock).mockResolvedValue({
      errors: {
        email: ["邮箱地址无效"],
        password: [
          "密码应至少包含一个大写字母。",
          "密码应至少包含一个特殊字符。",
        ],
      },
    });

    render(<Page />);

    const emailInput = screen.getByLabelText(/邮箱/i);
    const codeInput = screen.getByLabelText(/验证码/i);
    const passwordInput = screen.getByLabelText(/^密码$/i);
    const submitButton = screen.getByRole("button", { name: /注册/i });

    fireEvent.change(emailInput, { target: { value: "email@email.com" } });
    fireEvent.change(codeInput, { target: { value: "123456" } });
    fireEvent.change(passwordInput, { target: { value: "invalid_password" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("密码应至少包含一个大写字母。"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("密码应至少包含一个特殊字符。"),
      ).toBeInTheDocument();
      expect(screen.getByText("邮箱地址无效")).toBeInTheDocument();
    });

    const formData = new FormData();
    formData.set("email", "email@email.com");
    formData.set("code", "123456");
    formData.set("password", "invalid_password");
    expect(registerWithVerificationCode).toHaveBeenCalledWith(
      undefined,
      formData,
    );
  });
});
