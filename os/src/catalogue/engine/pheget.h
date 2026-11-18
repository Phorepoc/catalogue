// Copyright The Phorepoc Authors
// SPDX-License-Identifier: AGPL-3.0-only

// pheget.h -- OURS: the download app's engine (the format: the index repository's schema; the plan: pdk's
// `ph package`, which does the same from a computer). An index is a JSON file of items, each with its device
// compatibility and its approved releases (asset URL, size, SHA-256). The engine reads the device's identity, loads
// the indexes (HTTP(S) through the platform's HTTP stack, or a local file), downloads a release, checks its hash and
// installs it through the platform's software installer. The command line (pheget.cpp) and the UI share it.
#ifndef PHEGET_H
#define PHEGET_H

#include <e32base.h>
#include <f32file.h>
#include <es_sock.h>
#include <badesca.h>
#include <http/rhttpsession.h>
#include <http/mhttptransactioncallback.h>

class CPheJson;
namespace SwiUI { class RSWInstSilentLauncher; }

_LIT(KPheGetDefaultIndex, "https://phorepoc.github.io/index/index.json");
_LIT(KPheGetDeviceFile, "z:\\resource\\phorepoc\\device.txt");   // board=<name> / arch=<arm|x32>, from the adaptation
_LIT(KPheGetDir, "c:\\data\\pheget\\");                          // indexes.txt (extra indexes), installed.txt
_LIT(KPheGetDownloads, "c:\\data\\installs\\");                  // the package cache (prefill = offline installs)
// InstallL's answer when a listing (or one it requires) names a compatibility.min_core above the image's core= (device.txt)
const TInt KErrPheGetNeedsNewerSystem = -46201;
// InstallL's answer for a listing with compatibility.builtin_on_phorepoc on a Phorepoc image: the image provides it itself
const TInt KErrPheGetBuiltIn = -46202;
// SWI's KSWInstErrFileInUse (SWInstDefs.h): a file the package would install is in use, or the image's own copy of it
// has no ROM stub that lets the package replace it (KErrInvalidEclipsing)
const TInt KPheSwiErrFileInUse = -30477;

// One item of an index (pointers into the loaded index tree; valid while the engine is).
class TPheGetItem
	{
public:
	const CPheJson* iItem;
	const CPheJson* iRelease;       // the newest resolved release, or NULL
	TInt iIndex;                    // which loaded index it came from
	TPtrC8 Id() const;
	TPtrC8 Name() const;
	TPtrC8 Summary() const;
	TPtrC8 Category() const;
	TPtrC8 Tag() const;
	TPtrC8 Group() const;           // the listing's group: the package across its arches (phebrowser for phebrowser-x32)
	};

_LIT8(KPheGetInImage, "image");     // InstalledTagL: no install record, the image's own copy

class MPheGetObserver
	{
public:
	virtual void PheGetLog(const TDesC8& aLine) = 0;              // progress, one line
	virtual void PheGetProgress(TInt aDone, TInt aTotal) = 0;     // bytes of the current download (aTotal 0 = unknown, -1 = installing)
	};

class CPheGet : public CBase, public MHTTPTransactionCallback
	{
public:
	static CPheGet* NewL(MPheGetObserver& aObserver);
	~CPheGet();

	const TDesC8& Board() const { return iBoard; }
	const TDesC8& Arch() const { return iArch; }
	// ETrue on a Phorepoc image: the adaptation's device.txt exists (a stock phone has none).
	TBool IsPhorepoc() const { return iPhorepoc; }
	// ETrue when the listing says compatibility.builtin_on_phorepoc: Phorepoc OS provides the item itself.
	static TBool BuiltInOnPhorepoc(const CPheJson* aItem);
	// ETrue when this device is a Phorepoc one and the item is built in: such items are left out of ItemsL (unless aAll)
	// and never installed (InstallL: KErrPheGetBuiltIn), and a "requires" of one counts as met.
	TBool HiddenHere(const CPheJson* aItem) const { return iPhorepoc && BuiltInOnPhorepoc(aItem); }

	// Loads aExtra (may be empty), the default index (unless aNoDefault, or switched off while another source exists)
	// and the sources in c:\data\pheget\indexes.txt.
	// An index that fails is logged and skipped; leaves only if none loaded.
	// With aCachedOnly the URL indexes are read from their cache files (c:\data\pheget\ix<hash of the source>.json) and
	// nothing is downloaded: the instant start; RefreshIndexesL then updates the caches over the network.
	void LoadIndexesL(const TDesC& aExtra, TBool aNoDefault, TBool aCachedOnly = EFalse);
	// Downloads the URL indexes into their cache files; ETrue when one changed (reload then). Leaves when none could be fetched.
	TBool RefreshIndexesL(const TDesC& aExtra, TBool aNoDefault);
	// Fetches a file (URL or local path) into aFile, through a temporary name; returns the error (KErrNone = done).
	TInt FetchFileL(const TDesC& aLocation, const TDesC& aFile);
	void ResetIndexes() { iIndexes.ResetAndDestroy(); }    // (a refresh; invalidates every TPheGetItem)
	TInt IndexCount() const { return iIndexes.Count(); }   // the loaded indexes' top objects (categories, banner)
	const CPheJson& Index(TInt aIndex) const { return *iIndexes[aIndex]; }
	// The items that fit this device (all items with aAll), first index first; an id seen earlier wins.
	void ItemsL(RArray<TPheGetItem>& aItems, TBool aAll);
	TBool FindL(const TDesC8& aId, TPheGetItem& aItem);
	// Downloads (or reuses a cached copy with the right hash), verifies and installs silently; returns the
	// installer's result.
	TInt InstallL(const TPheGetItem& aItem, TChar aDrive);
	// The download half of InstallL: the release's package into the cache (or the cached copy), its hash checked;
	// aFile = the package. KErrNone = ready to install. Leaves on a failed fetch.
	TInt FetchPackageL(const TPheGetItem& aItem, TFileName& aFile);
	// The SIS package UID of an installed item: recorded at install (uids.txt), else read from its cached package;
	// 0 = unknown.
	TUint32 PackageUidL(const TPheGetItem& aItem);
	// Removes an installed item silently (SWI, by its package UID) and its install record; the installer's result.
	TInt UninstallL(const TPheGetItem& aItem);
	// The installed tag of an item (recorded by InstallL), or empty.
	void InstalledTagL(const TDesC8& aId, TDes8& aTag);
	// The same for an item, and with no record but the image carrying its group (its ROM stub, z:\system\install\<group>_stub.sis,
	// tools/rom_stubs.py) the tag KPheGetInImage: on the device, and any release replaces it (an update).
	void InstalledTagL(const TPheGetItem& aItem, TDes8& aTag);
	// The image's core version (device.txt "core=", YYYY.MM.DD.HHMMSS from the pdk), or empty (unknown: nothing is checked).
	const TDesC8& Core() const { return iCore; }
	// ETrue when the item, or a listing it requires (not yet installed), has a compatibility.min_core above Core().
	TBool NeedsNewerSystemL(const TPheGetItem& aItem);
	// Dotted versions compared field by field as numbers ("2026.11.10.165459" < "2026.11.11"): <0, 0, >0.
	static TInt CompareVersions(const TDesC8& aA, const TDesC8& aB);

	// ---- software sources: c:\data\pheget\indexes.txt (the default Phorepoc index is not in it; "#default=off" there
	// switches it off). Files are written atomically; the caches are named after their source, so removing a source
	// can never show its cache as another's.
	// ValidSource: an http(s) URL with a host, or a local path with a drive; ASCII, no spaces.
	static TBool ValidSource(const TDesC& aLocation);
	void SourcesL(CDesCArray& aSources);                  // the added sources, in order
	// EFalse when the default index is switched off. Off is honoured only while another source exists.
	TBool DefaultIndexEnabledL();
	void AddSourceL(const TDesC& aLocation);              // KErrArgument (not valid), KErrAlreadyExists
	void RemoveSourceL(TInt aIndex);                      // KErrNotFound; the last one gone puts the default index back on
	void SetDefaultIndexL(TBool aOn);                     // KErrNotSupported: off with no other source
	static void IndexCachePath(TDes& aFile, const TDesC& aLocation);   // the cache file of a source (URLs only)

	// MHTTPTransactionCallback
	void MHFRunL(RHTTPTransaction aTransaction, const THTTPEvent& aEvent);
	TInt MHFRunError(TInt aError, RHTTPTransaction aTransaction, const THTTPEvent& aEvent);

private:
	CPheGet(MPheGetObserver& aObserver) : iObserver(aObserver) {}
	void ConstructL();
	void ReadDeviceL();
	CDesCArray* LocationsL(const TDesC& aExtra, TBool aNoDefault);
	void PruneCaches();
	void ReadSourcesL(CDesCArray& aSources, TBool& aDefaultOff);
	void WriteSourcesL(const CDesCArray& aSources, TBool aDefaultOff);
	void LoadIndexL(const TDesC& aLocation, TBool aCachedOnly);
	void FetchL(const TDesC& aLocation, const TDesC& aFile);  // URL or local path -> aFile
	TInt SilentInstallAsync(SwiUI::RSWInstSilentLauncher& aLauncher, const TDesC& aFile, const TDesC8& aOptions);
	TInt SilentUninstallAsync(SwiUI::RSWInstSilentLauncher& aLauncher, TUid aUid, const TDesC8& aOptions);
	TUint32 SisUid(const TDesC& aFile);
	void SetLineL(const TDesC& aName, const TDesC8& aId, const TDesC8& aValue);   // aValue empty = remove the id
	void HttpGetL(const TDesC8& aUrl, const TDesC& aFile);
	void OpenNetworkL();
	TInt StartConnection();
	static TInt WatchTick(TAny* aSelf);       // the stalled-download watchdog
	TBool HashMatchesL(const TDesC& aFile, const TDesC8& aSha256Hex);
	void RecordInstalledL(const TDesC8& aId, const TDesC8& aTag);
	void Log(TRefByValue<const TDesC8> aFmt, ...);

	MPheGetObserver& iObserver;
	RFs iFs;
	TBuf8<32> iBoard;
	TBuf8<16> iArch;
	TBuf8<32> iCore;                           // device.txt core= (empty = unknown)
	TBool iPhorepoc;                           // device.txt exists: a Phorepoc image
	RPointerArray<CPheJson> iIndexes;
	HBufC8* iInstalledText;                    // installed.txt, read once (InstalledTagL)
	TBool iInstalledLoaded;
	TInt iDepth;                               // InstallL's "requires" recursion

	// network (opened on the first HTTP fetch)
	TBool iNetOpen;
	RSocketServ iSockServ;
	RConnection iConnection;
	RHTTPSession iSession;
	TBool iSessionOpen;

	// the HTTP fetch in progress
	CActiveSchedulerWait iWait;
	RFile iOut;
	TInt iHttpError;
	TInt iStatus;
	TInt iDone;
	TInt iTotal;
	RHTTPTransaction iTrans;                   // (for the watchdog's cancel)
	TUint32 iLastEvent;                        // User::NTickCount() of the last HTTP event
	TBool iTimedOut;
	};

#endif
