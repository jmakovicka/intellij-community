// Copyright 2000-2023 JetBrains s.r.o. and contributors. Use of this source code is governed by the Apache 2.0 license.
package com.intellij.pycharm.community.customization

import com.intellij.openapi.util.SystemInfo
import com.intellij.platform.ide.impl.customization.BaseJetBrainsExternalProductResourceUrls
import com.intellij.util.Url
import com.intellij.util.Urls

class PyCharmExternalResourceUrls : BaseJetBrainsExternalProductResourceUrls() {
  override val productPageUrl: Url
    get() = baseWebSiteUrl.resolve("pycharm/")

  override val basePatchDownloadUrl: Url
    get() = Urls.newFromEncoded("https://download.jetbrains.com/python/")

  override val baseWebHelpUrl: Url
    get() = baseWebSiteUrl.resolve("help/pycharm/")

  override val gettingStartedPageUrl: Url
    get() = baseWebSiteUrl.resolve("pycharm/learn/")

  override val keyboardShortcutsPdfUrl: Url
    get() {
      val suffix = if (SystemInfo.isMac) "_Mac" else ""
      return baseWebSiteUrl.resolve("pycharm/docs/PyCharm_ReferenceCard$suffix.pdf")
    }

  override val shortProductNameUsedInForms: String
    get() = "PyCharm"

  override val youtrackProjectId: String
    get() = "PY"

  override val youTubeChannelUrl: Url
    get() = Urls.newFromEncoded("https://www.youtube.com/@PyCharmIDE")
}